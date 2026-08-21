"""Проверки паспорта гонки: данные заполнены и не разъезжаются между языками."""

import pytest

from ubt_race_docs.race import (
    AWARDED_PLACES,
    CATEGORIES,
    RACE,
    Bilingual,
    place_title,
)


def test_all_bilingual_fields_are_filled() -> None:
    for field in (RACE.title, RACE.date, RACE.place, RACE.distance, RACE.discipline):
        assert field.ru.strip()
        assert field.kk.strip()


def test_one_line_joins_both_languages() -> None:
    assert Bilingual("Мужчины", "Ерлер").one_line() == "Мужчины · Ерлер"


def test_one_line_does_not_duplicate_identical_text() -> None:
    assert Bilingual("25 км", "25 км").one_line() == "25 км"
    assert Bilingual("25 км", "25 км").lines() == ("25 км",)


def test_categories_have_unique_codes() -> None:
    codes = [category.code for category in CATEGORIES]
    assert codes == sorted(set(codes), key=codes.index)
    assert len(codes) == len(CATEGORIES)


def test_place_title_is_bilingual() -> None:
    assert place_title(1) == Bilingual("1 место", "1-орын")
    assert place_title(3).kk == "3-орын"


def test_place_title_rejects_non_positive_place() -> None:
    with pytest.raises(ValueError, match="положительным"):
        place_title(0)


def test_site_url_is_the_root_of_the_race_page() -> None:
    assert RACE.url.startswith(RACE.site_url)
    assert RACE.site_url.count("/") == 3


def test_prize_rules_match_the_regulations() -> None:
    assert RACE.prizes.entry_fee == 1000
    assert RACE.prizes.tenge_per_second == 100
    assert RACE.prizes.payout_step == 1000


def test_certificates_cover_the_podium() -> None:
    assert AWARDED_PLACES == (1, 2, 3)
