"""Проверки паспорта гонки: данные заполнены и не разъезжаются между языками."""

import pytest

from ubt_race_docs.race import (
    AGE_GROUPS,
    AWARDED_PLACES,
    CATEGORIES,
    RACE,
    Bilingual,
    award_groups,
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


def test_chief_referee_is_filled_in() -> None:
    assert RACE.chief_referee == "Черных Денис"


def test_prize_rules_match_the_regulations() -> None:
    assert RACE.prizes.entry_fee == 1000
    assert RACE.prizes.tenge_per_second == 100
    assert RACE.prizes.payout_step == 1000


def test_certificates_cover_the_podium() -> None:
    assert AWARDED_PLACES == (1, 2, 3)


def test_age_groups_match_the_regulations() -> None:
    # По положению — четыре возрастные группы, одинаковые у мужчин и у женщин.
    assert len(AGE_GROUPS) == 4
    codes = [group.code for group in AGE_GROUPS]
    assert len(set(codes)) == len(codes)
    for group in AGE_GROUPS:
        assert "г.р." in group.name.ru
        assert group.name.kk != group.name.ru


def test_every_category_is_awarded_in_absolute_and_by_age() -> None:
    groups = award_groups()
    assert len(groups) == len(CATEGORIES) * (1 + len(AGE_GROUPS))
    assert len({group.code for group in groups}) == len(groups)

    absolute = [group for group in groups if group.age_group is None]
    assert [group.category for group in absolute] == list(CATEGORIES)
    assert absolute[0].title.ru == "Мужчины, абсолют"
    assert absolute[0].title.kk == "Ерлер, абсолют"


def test_age_group_title_names_both_the_sex_and_the_years() -> None:
    group = next(group for group in award_groups() if group.code == "women-1970")
    assert group.title.ru == "Женщины, 1970 г.р. и старше"
    assert group.title.kk == "Әйелдер, 1970 ж.т. және одан үлкен"
