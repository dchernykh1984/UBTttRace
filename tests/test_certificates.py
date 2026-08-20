"""Проверки грамот."""

from pathlib import Path

import pytest
from pypdf import PdfReader

from ubt_race_docs.certificates import SPARE_CERTIFICATES, build_certificates


@pytest.fixture(scope="module")
def pages(tmp_path_factory: pytest.TempPathFactory) -> list[str]:
    output = build_certificates(tmp_path_factory.mktemp("certs") / "certificates.pdf")
    return [page.extract_text() for page in PdfReader(output).pages]


def test_podium_of_both_categories_plus_spares(pages: list[str]) -> None:
    assert len(pages) == 2 * 3 + SPARE_CERTIFICATES


def test_every_sheet_is_a_certificate_of_this_race(pages: list[str]) -> None:
    for page in pages:
        assert "ГРАМОТА" in page
        assert "Открытая контрольная шоссейная тренировка" in page
        assert "UBT жеке стартпен" in page
        assert "Universal Bicycle Team" in page


def test_categories_and_places_are_pre_printed(pages: list[str]) -> None:
    printed = [
        (category, place)
        for category in ("Мужчины · Ерлер", "Женщины · Әйелдер")
        for place in ("1 место · 1-орын", "2 место · 2-орын", "3 место · 3-орын")
    ]
    for page, (category, place) in zip(pages, printed, strict=False):
        assert category in page
        assert place in page


def test_name_and_result_are_always_left_blank(pages: list[str]) -> None:
    for page in pages:
        assert "Фамилия · Тегі" in page
        assert "Имя · Аты" in page
        assert "Результат · Нәтижесі" in page


def test_spare_sheets_have_nothing_filled_in(pages: list[str]) -> None:
    for page in pages[-SPARE_CERTIFICATES:]:
        assert "Категория · Санаты" in page
        assert "Место · Орны" in page
        assert "Мужчины" not in page
        assert "1 место" not in page


def test_filled_sheets_have_no_empty_category_line(pages: list[str]) -> None:
    for page in pages[:-SPARE_CERTIFICATES]:
        assert "Категория · Санаты" not in page
        assert "Место · Орны" not in page


def test_spares_can_be_switched_off(tmp_path: Path) -> None:
    output = build_certificates(tmp_path / "certificates.pdf", spare=0)
    assert len(PdfReader(output).pages) == 6


def test_negative_spare_count_is_rejected(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="меньше нуля"):
        build_certificates(tmp_path / "certificates.pdf", spare=-1)
