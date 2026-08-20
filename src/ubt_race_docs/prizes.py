"""Расчёт призовых по положению гонки.

Фонд у мужчин и у женщин раздельный и целиком складывается из их стартовых
взносов. Каждая выигранная по протоколу секунда стоит 100 ₸: сначала победитель
получает за отрыв от второго, затем первые двое — за отрыв от третьего, и так
далее, пока фонд не кончится.

Шаг, на который денег уже не хватает, не оплачивается вовсе — распределение
на нём останавливается. Итоговая сумма каждого округляется вниз до 1000 ₸,
чтобы выдавать наличными тысячными купюрами и не выйти за фонд.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from itertools import pairwise

from .race import RACE, PrizeRules


@dataclass(frozen=True, slots=True)
class Result:
    """Строка протокола: кто и с каким временем финишировал."""

    name: str
    seconds: float
    bib: int | None = None


@dataclass(frozen=True, slots=True)
class Step:
    """Шаг распределения: отрыв между местами `index` и `index + 1`."""

    index: int
    gap: float
    cost: float
    cumulative: float
    funded: bool


@dataclass(frozen=True, slots=True)
class Payout:
    """Сколько получает участник на месте `place`."""

    place: int
    result: Result
    raw: float
    amount: int


@dataclass(frozen=True, slots=True)
class Distribution:
    """Итог распределения фонда."""

    fund: int
    steps: tuple[Step, ...]
    payouts: tuple[Payout, ...]

    @property
    def total_paid(self) -> int:
        return sum(payout.amount for payout in self.payouts)

    @property
    def remainder(self) -> int:
        return self.fund - self.total_paid

    @property
    def winners(self) -> tuple[Payout, ...]:
        """Только те, кому что-то досталось."""
        return tuple(payout for payout in self.payouts if payout.amount > 0)


def fund_from_entries(entries: int, rules: PrizeRules = RACE.prizes) -> int:
    """Призовой фонд категории: все её стартовые взносы."""
    if entries < 0:
        raise ValueError(f"число взносов не может быть отрицательным, получено {entries}")
    return entries * rules.entry_fee


def _steps(results: Sequence[Result], fund: int, rules: PrizeRules) -> tuple[Step, ...]:
    steps: list[Step] = []
    cumulative = 0.0
    for index in range(1, len(results)):
        gap = results[index].seconds - results[index - 1].seconds
        cost = index * gap * rules.tenge_per_second
        cumulative += cost
        steps.append(
            Step(
                index=index,
                gap=gap,
                cost=cost,
                cumulative=cumulative,
                funded=cumulative <= fund,
            )
        )
    return tuple(steps)


def distribute(
    results: Sequence[Result],
    fund: int,
    rules: PrizeRules = RACE.prizes,
) -> Distribution:
    """Разложить `fund` по участникам `results`, упорядоченным по времени."""
    if fund < 0:
        raise ValueError(f"призовой фонд не может быть отрицательным, получен {fund}")
    for previous, current in pairwise(results):
        if current.seconds < previous.seconds:
            raise ValueError(
                "результаты должны идти по возрастанию времени: "
                f"{current.name} ({current.seconds} с) стоит после "
                f"{previous.name} ({previous.seconds} с)"
            )

    steps = _steps(results, fund, rules)
    payouts: list[Payout] = []
    for place, result in enumerate(results, start=1):
        raw = sum(
            step.gap * rules.tenge_per_second
            for step in steps
            if step.funded and step.index >= place
        )
        amount = int(raw // rules.payout_step) * rules.payout_step
        payouts.append(Payout(place=place, result=result, raw=raw, amount=amount))

    return Distribution(fund=fund, steps=steps, payouts=tuple(payouts))
