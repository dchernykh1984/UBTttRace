"""Проверки стартовых номеров."""

from pathlib import Path

import pytest
from pypdf import PdfReader

from ubt_race_docs.bibs import (
    BibLayout,
    build_bibs,
    number_font_size,
    number_stretch,
)
from ubt_race_docs.fonts import NUMBER, cap_height, text_width

MM = 72 / 25.4


@pytest.fixture(scope="module")
def small_run(tmp_path_factory: pytest.TempPathFactory) -> Path:
    output = tmp_path_factory.mktemp("bibs") / "bibs.pdf"
    return build_bibs(output, first=1, last=5)


def test_two_numbers_per_sheet(small_run: Path) -> None:
    assert len(PdfReader(small_run).pages) == 3


def test_every_number_is_printed_twice(small_run: Path) -> None:
    lines = [
        line for page in PdfReader(small_run).pages for line in page.extract_text().splitlines()
    ]
    for number in range(1, 6):
        assert lines.count(str(number)) == 2, f"номер {number} напечатан не дважды"


def test_sheet_carries_nothing_but_the_numbers(small_run: Path) -> None:
    # На номере не должно быть служебных подписей: он и так понятен,
    # а лишний текст только мешает читать цифры с обочины.
    first_page = PdfReader(small_run).pages[0].extract_text()
    for caption in ("Стартовый номер", "линия разреза", "линия сгиба", "04.10.2026"):
        assert caption not in first_page


def test_widest_number_fits_the_tail() -> None:
    layout = BibLayout()
    size = number_font_size(layout, 3)
    assert text_width("300", NUMBER, size) == pytest.approx(layout.number_width)


def test_digits_are_large_enough_to_read_from_the_roadside() -> None:
    layout = BibLayout()
    size = number_font_size(layout, 3)
    height = cap_height(NUMBER, size) * number_stretch(layout, size)
    assert height / MM > 60


def test_digits_stay_inside_the_strip() -> None:
    layout = BibLayout()
    size = number_font_size(layout, 3)
    height = cap_height(NUMBER, size) * number_stretch(layout, size)
    assert height <= layout.band_height


def test_number_font_size_needs_digits() -> None:
    with pytest.raises(ValueError, match="хотя бы одна цифра"):
        number_font_size(BibLayout(), 0)


def test_range_is_validated(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="номера начинаются с 1"):
        build_bibs(tmp_path / "a.pdf", first=0, last=10)
    with pytest.raises(ValueError, match="меньше первого"):
        build_bibs(tmp_path / "b.pdf", first=10, last=9)


def test_single_number_still_makes_a_sheet(tmp_path: Path) -> None:
    output = build_bibs(tmp_path / "one.pdf", first=7, last=7)
    reader = PdfReader(output)
    assert len(reader.pages) == 1
    assert reader.pages[0].extract_text().count("7") == 2


def test_output_directory_is_created(tmp_path: Path) -> None:
    output = build_bibs(tmp_path / "deep" / "dir" / "bibs.pdf", first=1, last=1)
    assert output.is_file()
