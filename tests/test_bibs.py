"""Проверки стартовых номеров."""

from pathlib import Path

import pytest
from pypdf import PdfReader

from ubt_race_docs import bibs
from ubt_race_docs.bibs import (
    BibLayout,
    build_bibs,
    number_font_size,
    number_stretch,
)
from ubt_race_docs.fonts import NUMBER, cap_height, text_width
from ubt_race_docs.race import RACE

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


def test_wrap_allowance_covers_a_full_turn_around_the_seat_tube() -> None:
    # Хвосты обходят трубу каждый на половину периметра и смыкаются за ней,
    # иначе номер сползает. 34 мм — толстая круглая подседельная труба.
    layout = BibLayout()
    assert layout.wraps_tube_of_diameter(34 * MM)
    assert not layout.wraps_tube_of_diameter(60 * MM)


def test_digits_begin_only_past_the_wrap_zone() -> None:
    layout = BibLayout()
    tail_start = layout.center_x + layout.wrap_allowance
    assert tail_start + layout.number_width + layout.outer_margin == pytest.approx(
        layout.page_width
    )


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


def test_logo_sits_on_the_fold(small_run: Path) -> None:
    # Логотип печатается на каждой полоске и оказывается спереди на трубе,
    # поэтому он должен целиком помещаться в зону обхвата.
    assert PdfReader(small_run).pages[0].images
    layout = BibLayout()
    assert layout.logo_size + 2 * layout.logo_gap < 2 * layout.wrap_allowance


def test_wordmark_replaces_the_old_caption(small_run: Path) -> None:
    assert PdfReader(small_run).pages[0].extract_text().count(RACE.short_title) == 4


def test_each_tail_carries_a_qr_to_the_race_page(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls: list[tuple[float, float, float, str]] = []
    monkeypatch.setattr(
        bibs,
        "qr_code",
        lambda canvas, x, y, size, url: calls.append((x, y, size, url)),
    )
    build_bibs(tmp_path / "bibs.pdf", first=1, last=1)

    assert len(calls) == 2, "QR нужен на обоих хвостах — номер читают с двух сторон"
    assert {call[3] for call in calls} == {RACE.url}

    # QR стоит в дальнем от сгиба углу, чтобы не попасть в зону обхвата трубы.
    layout = BibLayout()
    left_qr, right_qr = sorted(call[0] for call in calls)
    assert left_qr == pytest.approx(layout.outer_margin)
    assert right_qr == pytest.approx(layout.page_width - layout.outer_margin - layout.qr_size)


def test_qr_modules_stay_printable() -> None:
    # Модуль мельче 0.5 мм телефон уже читает плохо.
    modules = 33
    assert BibLayout().qr_size / modules > 0.5 * (72 / 25.4)
