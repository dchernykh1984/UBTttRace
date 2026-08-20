"""Проверки распределения призового фонда."""

import pytest

from ubt_race_docs.prizes import (
    Result,
    distribute,
    fund_from_entries,
)
from ubt_race_docs.race import RACE, PrizeRules

RULES = RACE.prizes


def results(*seconds: float) -> list[Result]:
    return [
        Result(name=f"Участник {index}", seconds=value) for index, value in enumerate(seconds, 1)
    ]


def test_fund_is_the_sum_of_entry_fees() -> None:
    assert fund_from_entries(40) == 40_000
    assert fund_from_entries(0) == 0


def test_negative_entries_are_rejected() -> None:
    with pytest.raises(ValueError, match="отрицательным"):
        fund_from_entries(-1)


def test_winner_is_paid_for_the_gap_to_the_second() -> None:
    distribution = distribute(results(3600, 3662), fund=40_000)
    assert distribution.payouts[0].raw == 6_200
    assert distribution.payouts[0].amount == 6_000
    assert distribution.payouts[1].amount == 0


def test_each_step_is_shared_by_everyone_above_it() -> None:
    # Отрывы 62, 31 и 15 секунд: шаги стоят 6200, 6200 и 4500 ₸.
    distribution = distribute(results(3600, 3662, 3693, 3708), fund=40_000)
    assert [step.cost for step in distribution.steps] == [6_200, 6_200, 4_500]
    assert [step.cumulative for step in distribution.steps] == [6_200, 12_400, 16_900]
    assert all(step.funded for step in distribution.steps)
    assert [payout.raw for payout in distribution.payouts] == [10_800, 4_600, 1_500, 0]
    assert [payout.amount for payout in distribution.payouts] == [10_000, 4_000, 1_000, 0]


def test_payout_never_exceeds_the_fund() -> None:
    distribution = distribute(results(*range(3600, 3600 + 60 * 30, 30)), fund=20_000)
    assert distribution.total_paid <= distribution.fund
    assert distribution.remainder >= 0


def test_step_that_does_not_fit_is_not_paid_at_all() -> None:
    # Первый шаг стоит 6200, второй — 6200: на второй остатка (3800) не хватает.
    distribution = distribute(results(3600, 3662, 3693), fund=10_000)
    assert [step.funded for step in distribution.steps] == [True, False]
    assert [payout.amount for payout in distribution.payouts] == [6_000, 0, 0]


def test_distribution_stops_and_does_not_skip_to_a_cheaper_step() -> None:
    # Третий шаг дешёвый, но идти дальше уже нельзя: фонд кончился на втором.
    distribution = distribute(results(0, 62, 124, 124.5), fund=10_000)
    assert [step.funded for step in distribution.steps] == [True, False, False]


def test_prizes_do_not_grow_down_the_protocol() -> None:
    distribution = distribute(results(0, 40, 95, 130, 131, 400), fund=60_000)
    amounts = [payout.amount for payout in distribution.payouts]
    assert amounts == sorted(amounts, reverse=True)


def test_equal_times_get_equal_money() -> None:
    distribution = distribute(results(3600, 3600, 3700), fund=40_000)
    first, second, third = distribution.payouts
    assert first.amount == second.amount
    assert third.amount == 0


def test_single_finisher_gets_nothing_to_win_seconds_from() -> None:
    distribution = distribute(results(3600), fund=40_000)
    assert distribution.payouts[0].amount == 0
    assert distribution.steps == ()


def test_empty_protocol_is_allowed() -> None:
    distribution = distribute([], fund=40_000)
    assert distribution.payouts == ()
    assert distribution.remainder == 40_000
    assert distribution.winners == ()


def test_zero_fund_pays_nobody() -> None:
    distribution = distribute(results(3600, 3700), fund=0)
    assert distribution.total_paid == 0


def test_protocol_must_be_sorted_by_time() -> None:
    with pytest.raises(ValueError, match="по возрастанию времени"):
        distribute(results(3700, 3600), fund=40_000)


def test_negative_fund_is_rejected() -> None:
    with pytest.raises(ValueError, match="не может быть отрицательным"):
        distribute(results(3600), fund=-1)


def test_rules_are_configurable() -> None:
    rules = PrizeRules(entry_fee=500, tenge_per_second=10, payout_step=100)
    distribution = distribute(results(0, 62), fund=fund_from_entries(10, rules), rules=rules)
    assert distribution.fund == 5_000
    assert distribution.payouts[0].raw == 620
    assert distribution.payouts[0].amount == 600


def test_winners_are_only_those_with_money() -> None:
    distribution = distribute(results(0, 62, 93), fund=40_000)
    assert [payout.place for payout in distribution.winners] == [1, 2]
