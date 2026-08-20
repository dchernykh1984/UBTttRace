"""Регистрация шрифтов для PDF.

Стандартные шрифты reportlab не умеют кириллицу, поэтому все документы рисуются
шрифтами DejaVu, которые лежат рядом в `assets/fonts`.
"""

from __future__ import annotations

from pathlib import Path

from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

FONT_DIR = Path(__file__).parent / "assets" / "fonts"

SANS = "DejaVuSans"
SANS_BOLD = "DejaVuSans-Bold"
NUMBER = "DejaVuSansCondensed-Bold"
TITLE = "DejaVuSerif-Bold"

FONT_FILES: dict[str, str] = {
    SANS: "DejaVuSans.ttf",
    SANS_BOLD: "DejaVuSans-Bold.ttf",
    NUMBER: "DejaVuSansCondensed-Bold.ttf",
    TITLE: "DejaVuSerif-Bold.ttf",
}

_registered = False


def register_fonts() -> None:
    """Зарегистрировать шрифты в reportlab. Повторные вызовы безопасны."""
    global _registered
    if _registered:
        return

    for name, filename in FONT_FILES.items():
        path = FONT_DIR / filename
        if not path.is_file():
            raise FileNotFoundError(f"нет файла шрифта {path}")
        pdfmetrics.registerFont(TTFont(name, str(path)))

    # Чтобы <b> внутри Paragraph брал именно жирный DejaVu.
    pdfmetrics.registerFontFamily(
        SANS, normal=SANS, bold=SANS_BOLD, italic=SANS, boldItalic=SANS_BOLD
    )
    _registered = True


def text_width(text: str, font: str, size: float) -> float:
    """Ширина строки в пунктах."""
    register_fonts()
    width: float = pdfmetrics.stringWidth(text, font, size)
    return width


def cap_height(font: str, size: float) -> float:
    """Высота заглавных букв и цифр в пунктах — по ней центрируем крупный текст."""
    register_fonts()
    face = pdfmetrics.getFont(font).face
    return float(face.capHeight) / 1000.0 * size
