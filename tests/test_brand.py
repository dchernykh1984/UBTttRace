"""Проверки фирменного стиля."""

from pathlib import Path

from PIL import Image
from pypdf import PdfReader
from reportlab.lib import colors
from reportlab.pdfgen.canvas import Canvas

from ubt_race_docs.brand import BLUE, GREEN, INK, LOGO_PATH, ORANGE, PAPER, draw_logo

MM = 72 / 25.4


def brightness(colour: colors.Color) -> float:
    """Воспринимаемая яркость цвета, 0 — чёрный, 1 — белый."""
    return 0.299 * colour.red + 0.587 * colour.green + 0.114 * colour.blue


def test_logo_is_shipped_with_the_package() -> None:
    assert LOGO_PATH.is_file()
    assert LOGO_PATH.stat().st_size > 0


def test_palette_comes_from_the_logo_and_the_jersey() -> None:
    assert ORANGE.hexval() == "0xf08020"
    assert BLUE.hexval() == "0x2030b0"
    assert GREEN.hexval() == "0x33b012"
    # Лист светлый, текст тёмный — иначе на печати всё поплывёт.
    assert brightness(PAPER) > 0.9
    assert brightness(INK) < 0.2


def test_logo_lands_on_the_page(tmp_path: Path) -> None:
    output = tmp_path / "logo.pdf"
    canvas = Canvas(str(output))
    draw_logo(canvas, 100, 100, 40)
    canvas.showPage()
    canvas.save()
    assert len(PdfReader(output).pages[0].images) == 1


def test_logo_has_a_transparent_background() -> None:
    # На кремовом листе грамоты белая подложка логотипа была бы видна.
    with Image.open(LOGO_PATH) as logo:
        assert logo.mode == "RGBA"
        assert logo.getchannel("A").getpixel((0, 0)) == 0
        assert min(logo.size) >= 800
