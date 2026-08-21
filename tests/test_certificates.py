"""Проверки грамот."""

from pathlib import Path

import pytest
from PIL import Image
from pypdf import PdfReader
from reportlab.lib.units import mm

from ubt_race_docs.background import BackgroundStyle
from ubt_race_docs.certificates import (
    SPARE_CERTIFICATES,
    CertificateLayout,
    build_certificates,
)
from ubt_race_docs.race import RACE


@pytest.fixture(scope="module")
def certificates(tmp_path_factory: pytest.TempPathFactory) -> Path:
    return build_certificates(tmp_path_factory.mktemp("certs") / "certificates.pdf")


@pytest.fixture(scope="module")
def pages(certificates: Path) -> list[str]:
    return [page.extract_text() for page in PdfReader(certificates).pages]


def test_every_sheet_is_printed_on_the_branded_background(certificates: Path) -> None:
    for page in PdfReader(certificates).pages:
        assert page.images, "на листе нет водяного знака — значит нет и фона"


def test_podium_of_both_categories_plus_spares(pages: list[str]) -> None:
    assert len(pages) == 2 * 3 + SPARE_CERTIFICATES


def test_every_sheet_is_a_certificate_of_this_race(pages: list[str]) -> None:
    for page in pages:
        assert "ГРАМОТА" in page
        assert "Открытая контрольная шоссейная тренировка" in page
        assert "UBT жеке стартпен" in page
        assert "Universal Bicycle Team" in page
        # Ссылка должна пережить эту гонку, поэтому ведёт на корень сайта.
        assert RACE.site_url in page
        assert RACE.url not in page


def test_categories_and_places_are_pre_printed(pages: list[str]) -> None:
    printed = [
        (category, place)
        for category in ("Мужчины · Ерлер", "Женщины · Әйелдер")
        for place in ("1 место · 1-орын", "2 место · 2-орын", "3 место · 3-орын")
    ]
    for page, (category, place) in zip(pages, printed, strict=False):
        assert category in page
        assert place in page


def test_chief_referee_is_printed_above_the_line(pages: list[str]) -> None:
    for page in pages:
        assert RACE.chief_referee in page
        assert "Главный судья · Бас төреші" in page
        # Имя идёт первым: над чертой, как и всё, что вписывают от руки.
        assert page.index(RACE.chief_referee) < page.index("Главный судья")


def test_signature_line_is_shorter_than_the_fields(pages: list[str]) -> None:
    layout = CertificateLayout()
    assert layout.signature_width < layout.field_width


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


def test_own_picture_replaces_the_drawn_background(tmp_path: Path) -> None:
    picture = tmp_path / "фон.png"
    Image.new("RGB", (400, 560), "white").save(picture)

    output = build_certificates(tmp_path / "certificates.pdf", spare=0, background=picture)
    images = PdfReader(output).pages[0].images
    assert len(images) == 1, "поверх своей картинки водяной знак уже не нужен"
    embedded = images[0].image
    assert embedded is not None
    assert embedded.size == (400, 560)


def test_missing_background_is_reported(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="нет файла фона"):
        build_certificates(tmp_path / "certificates.pdf", background=tmp_path / "нет.png")


def test_nothing_is_printed_over_the_frame() -> None:
    # Самая нижняя строка грамоты — подвал; он должен остаться внутри рамки.
    layout = CertificateLayout()
    style = BackgroundStyle()
    footer_baseline = layout.page_height - layout.footer_y - 11
    assert footer_baseline > style.frame_margin + style.frame_inset + 2 * mm
