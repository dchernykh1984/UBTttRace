"""Проверки распределения призового фонда."""

import random

import pytest

from ubt_race_docs.prizes import (
    Result,
    distribute,
    even_threshold,
    fund_from_entries,
    round_to_step,
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


def test_rounding_goes_to_the_nearest_thousand() -> None:
    assert round_to_step(2730, 1000) == 3000
    assert round_to_step(650, 1000) == 1000
    assert round_to_step(490, 1000) == 0
    assert round_to_step(500, 1000) == 1000
    assert round_to_step(1500, 1000) == 2000


def test_real_protocol_spends_the_whole_fund() -> None:
    # Протокол мужской группы: четыре финишера, фонд из четырёх взносов.
    distribution = distribute(results(1766.1, 1786.9, 1793.4, 1821.9), fund_from_entries(4))
    assert [payout.amount for payout in distribution.payouts] == [3000, 1000, 0, 0]
    assert distribution.total_paid == distribution.fund
    assert distribution.remainder == 0


def test_payout_never_exceeds_the_fund() -> None:
    distribution = distribute(results(*range(3600, 3600 + 60 * 30, 30)), fund=20_000)
    assert distribution.total_paid <= distribution.fund


def test_prizes_do_not_grow_down_the_protocol() -> None:
    distribution = distribute(results(0, 40, 95, 130, 131, 400), fund=60_000)
    amounts = [payout.amount for payout in distribution.payouts]
    assert amounts == sorted(amounts, reverse=True)


def test_equal_times_get_equal_money() -> None:
    distribution = distribute(results(3600, 3600, 3700), fund=40_000)
    first, second, _ = distribution.payouts
    assert first.amount == second.amount


def test_single_finisher_takes_the_fund() -> None:
    # Обгонять некого, но фонд собран из взносов и должен уйти победителю.
    distribution = distribute(results(3600), fund=5_000)
    assert distribution.payouts[0].amount == 5_000
    assert distribution.remainder == 0


def test_lonely_leader_with_a_huge_gap() -> None:
    distribution = distribute(results(3600, 7200), fund=4_000)
    assert [payout.amount for payout in distribution.payouts] == [4000, 0]
    assert distribution.remainder == 0


def test_empty_protocol_is_allowed() -> None:
    distribution = distribute([], fund=40_000)
    assert distribution.payouts == ()
    assert distribution.remainder == 40_000


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
    assert distribution.total_paid == 5_000


def test_threshold_without_rounding_spends_the_fund_exactly() -> None:
    protocol = results(1766.1, 1786.9, 1793.4, 1821.9)
    threshold = even_threshold(protocol, 4_000, RULES)
    raw = sum(max(0.0, threshold - result.seconds) * RULES.tenge_per_second for result in protocol)
    assert raw == pytest.approx(4_000)


def test_thousand_goes_to_the_first_rider_left_without_money() -> None:
    # Трое с одинаковым временем: округление не даёт попасть в фонд точно.
    distribution = distribute(results(1000.0, 1000.0, 1000.0, 2000.0), fund=4_000)
    assert distribution.leftover_place == 4
    assert distribution.payouts[3].amount == 1000
    assert distribution.total_paid <= distribution.fund


@pytest.mark.parametrize("riders", [1, 2, 3, 7, 25, 60])
def test_fund_is_spent_completely_on_realistic_protocols(riders: int) -> None:
    # Времена «раздельного старта» на 25 км: около получаса и десятки секунд
    # разброса. На таких данных фонд должен уходить целиком.
    random.seed(riders)
    seconds = sorted(round(random.uniform(1700, 2600), 1) for _ in range(riders))
    fund = fund_from_entries(riders)
    distribution = distribute(results(*seconds), fund)
    assert distribution.total_paid == fund, f"{riders} гонщиков: остаток {distribution.remainder}"


@pytest.mark.parametrize("seed", range(40))
def test_distribution_holds_together_on_random_protocols(seed: int) -> None:
    random.seed(seed)
    riders = random.randint(1, 40)
    seconds = sorted(round(random.uniform(1500, 3000), 1) for _ in range(riders))
    fund = fund_from_entries(random.randint(riders, riders + 30))

    distribution = distribute(results(*seconds), fund)
    amounts = [payout.amount for payout in distribution.payouts]

    assert distribution.total_paid <= fund, "выплаты не должны превышать фонд"
    assert amounts == sorted(amounts, reverse=True), "ниже по протоколу — не больше денег"
    assert all(amount % RULES.payout_step == 0 for amount in amounts), "выдаём тысячными купюрами"
    assert distribution.remainder == 0 or distribution.leftover_place is not None
