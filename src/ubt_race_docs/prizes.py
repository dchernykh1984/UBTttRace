"""Расчёт призовых по положению гонки.

Фонд у мужчин и у женщин раздельный и целиком складывается из их стартовых
взносов. Каждая выигранная секунда стоит 100 ₸, и считаются они от порогового
времени: участник получает за столько секунд, на сколько опередил порог.

Порог не берётся с потолка — он подбирается так, чтобы фонд разошёлся целиком.
Суммы округляются до ближайшей тысячи (наличные выдаются тысячными купюрами),
и порог двигается с шагом в десятую долю секунды, пока сумма всех выплат
не сравняется с фондом.

Так распределение остаётся тем же по духу, что и в положении: победитель
получает за отрыв от второго, первые двое — за отрыв от третьего и так далее.
Разница в том, что порог может встать не ровно на чьё-то время, а между —
за счёт этого фонд уходит без остатка.

Если из-за округления попасть точно в фонд нельзя (так бывает, когда несколько
участников показали совпадающее до десятой доли время), лишняя тысяча уходит
первому из тех, кому ничего не досталось, а всё сверх неё остаётся в фонде.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from itertools import pairwise
from math import floor, inf

from .race import RACE, PrizeRules

TIME_STEP = 0.1
"""Шаг подбора порога: протоколы печатаются с точностью до десятой доли."""

TIME_DIGITS = 6
"""До скольких знаков приводится порог.

Без этого 21152 × 0.1 даёт 2115.2000000000003, и участник, стоящий ровно
на границе округления, случайно перескакивает через неё — расчёт разъезжается
с тем, что считает книга.
"""


@dataclass(frozen=True, slots=True)
class Result:
    """Строка протокола: кто и с каким временем финишировал."""

    name: str
    seconds: float
    bib: int | None = None


@dataclass(frozen=True, slots=True)
class Payout:
    """Сколько получает участник на месте `place`."""

    place: int
    result: Result
    raw: float
    amount: int

    @property
    def ahead_of_threshold(self) -> float:
        """На сколько секунд участник опередил пороговое время."""
        return self.raw / RACE.prizes.tenge_per_second


@dataclass(frozen=True, slots=True)
class Distribution:
    """Итог распределения фонда."""

    fund: int
    threshold: float
    payouts: tuple[Payout, ...]
    leftover_place: int | None = None
    """Место, которому досталась тысяча нераспределённого остатка."""

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


def round_to_step(amount: float, step: int) -> int:
    """Округление до ближайшего шага; ровная половина идёт вверх."""
    return floor(amount / step + 0.5) * step


def payout_at(threshold: float, seconds: float, rules: PrizeRules) -> int:
    """Сколько получит участник с таким временем при таком пороге."""
    ahead = max(0.0, threshold - seconds)
    return round_to_step(ahead * rules.tenge_per_second, rules.payout_step)


def total_at(threshold: float, results: Sequence[Result], rules: PrizeRules) -> int:
    """Сумма всех выплат при данном пороге."""
    return sum(payout_at(threshold, result.seconds, rules) for result in results)


def even_threshold(results: Sequence[Result], fund: int, rules: PrizeRules) -> float:
    """Порог, при котором выплаты **без округления** дают ровно фонд.

    Если призовые получают `m` первых участников, то сумма выплат равна
    `(m·T − Σt) · цена секунды`. Отсюда `T` для каждого `m` считается напрямую,
    а верным будет тот `m`, при котором порог попадает между временем `m`-го
    участника и следующего за ним.
    """
    times = sorted(result.seconds for result in results)
    target = fund / rules.tenge_per_second
    running = 0.0
    threshold = times[0]
    for index, current in enumerate(times):
        running += current
        candidate = (target + running) / (index + 1)
        following = times[index + 1] if index + 1 < len(times) else inf
        threshold = candidate
        if current < candidate <= following:
            break
    return threshold


def on_grid(tenths: int) -> float:
    """Порог по номеру десятой доли, без хвостов плавающей арифметики."""
    return round(tenths * TIME_STEP, TIME_DIGITS)


def fitting_threshold(results: Sequence[Result], fund: int, rules: PrizeRules) -> float:
    """Наибольший порог (с точностью до десятой), при котором выплаты влезают в фонд.

    Сумма выплат по порогу не убывает, поэтому границу ищем двоичным поиском.
    """
    fastest = min(result.seconds for result in results)
    low = floor(fastest / TIME_STEP)
    high = floor(even_threshold(results, fund, rules) / TIME_STEP) + 200

    while low < high:
        middle = (low + high + 1) // 2
        if total_at(on_grid(middle), results, rules) <= fund:
            low = middle
        else:
            high = middle - 1
    return on_grid(low)


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

    if not results:
        return Distribution(fund=fund, threshold=0.0, payouts=())

    threshold = fitting_threshold(results, fund, rules) if fund else results[0].seconds
    payouts = [
        Payout(
            place=place,
            result=result,
            raw=max(0.0, threshold - result.seconds) * rules.tenge_per_second,
            amount=payout_at(threshold, result.seconds, rules),
        )
        for place, result in enumerate(results, start=1)
    ]

    leftover_place = None
    leftover = fund - sum(payout.amount for payout in payouts)
    if leftover >= rules.payout_step:
        for index, payout in enumerate(payouts):
            if payout.amount == 0:
                payouts[index] = Payout(
                    place=payout.place,
                    result=payout.result,
                    raw=payout.raw,
                    amount=rules.payout_step,
                )
                leftover_place = payout.place
                break

    return Distribution(
        fund=fund,
        threshold=threshold,
        payouts=tuple(payouts),
        leftover_place=leftover_place,
    )
