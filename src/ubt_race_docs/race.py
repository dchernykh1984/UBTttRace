"""Постоянные данные гонки и двуязычные (RU/KZ) подписи.

Единственное место, где заданы название, дата, место и денежные правила.
Все генераторы документов берут их отсюда, чтобы данные не расходились между
номерами, грамотами, расписками и таблицей призовых.
"""

from __future__ import annotations

from dataclasses import dataclass

SEPARATOR = " · "
"""Разделитель русской и казахской версии подписи в одну строку."""


@dataclass(frozen=True, slots=True)
class Bilingual:
    """Подпись на двух языках."""

    ru: str
    kk: str

    def one_line(self, separator: str = SEPARATOR) -> str:
        """Обе версии в одну строку — для мелких подписей."""
        if self.ru == self.kk:
            return self.ru
        return f"{self.ru}{separator}{self.kk}"

    def lines(self) -> tuple[str, ...]:
        """Обе версии отдельными строками — для крупного текста."""
        if self.ru == self.kk:
            return (self.ru,)
        return (self.ru, self.kk)


@dataclass(frozen=True, slots=True)
class Category:
    """Зачётная категория участников."""

    code: str
    name: Bilingual
    winner: Bilingual
    """Как называется победитель этой категории — надпись на кубке."""


@dataclass(frozen=True, slots=True)
class PrizeRules:
    """Денежные правила из положения гонки."""

    entry_fee: int
    """Стартовый взнос, ₸. Целиком уходит в призовой фонд."""

    tenge_per_second: int
    """Столько стоит одна выигранная по протоколу секунда."""

    payout_step: int
    """Шаг округления выплаты, ₸. Итог округляется вниз до кратного."""


@dataclass(frozen=True, slots=True)
class RaceInfo:
    """Паспорт гонки."""

    title: Bilingual
    short_title: str
    date: Bilingual
    date_numeric: str
    place: Bilingual
    distance: Bilingual
    discipline: Bilingual
    organizer: str
    chief_referee: str
    """Главный судья: его имя печатается на грамотах под линией для подписи."""

    url: str
    """Страница гонки — на неё ведёт QR со стартового номера."""

    site_url: str
    """Корень сайта команды — его печатаем там, где ссылка должна пережить гонку."""

    prizes: PrizeRules


# По-казахски «жеңімпаз» одинаково для мужчин и женщин, род не меняется.
CATEGORY_MEN = Category(
    code="men",
    name=Bilingual("Мужчины", "Ерлер"),
    winner=Bilingual("Победитель", "Жеңімпаз"),
)
CATEGORY_WOMEN = Category(
    code="women",
    name=Bilingual("Женщины", "Әйелдер"),
    winner=Bilingual("Победительница", "Жеңімпаз"),
)

CATEGORIES: tuple[Category, ...] = (CATEGORY_MEN, CATEGORY_WOMEN)

AWARDED_PLACES: tuple[int, ...] = (1, 2, 3)
"""Места, за которые вручаются грамоты (по положению — первая тройка)."""


def place_title(place: int) -> Bilingual:
    """Подпись места: «1 место» / «1-орын»."""
    if place < 1:
        raise ValueError(f"место должно быть положительным, получено {place}")
    return Bilingual(f"{place} место", f"{place}-орын")


RACE = RaceInfo(
    title=Bilingual(
        "Открытая контрольная шоссейная тренировка с раздельным стартом UBT",
        "UBT жеке стартпен өтетін ашық бақылау шоссе жаттығуы",
    ),
    short_title="UBT TT",
    date=Bilingual("4 октября 2026 года", "2026 жылғы 4 қазан"),
    date_numeric="04.10.2026",
    place=Bilingual(
        "Алматинская область, село Кырбалтабай",
        "Алматы облысы, Қырбалтабай ауылы",
    ),
    distance=Bilingual("25 км", "25 км"),
    discipline=Bilingual(
        "индивидуальная гонка с раздельного старта",
        "жеке стартпен өтетін жарыс",
    ),
    organizer="Universal Bicycle Team",
    chief_referee="Черных Денис",
    url="https://universalbicycle.team/calendar/533/",
    site_url="https://universalbicycle.team/",
    prizes=PrizeRules(entry_fee=1000, tenge_per_second=100, payout_step=1000),
)
