"""Проверки шрифтов: файлы на месте и покрывают казахские буквы."""

from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from ubt_race_docs.fonts import (
    FONT_DIR,
    FONT_FILES,
    NUMBER,
    SANS,
    cap_height,
    register_fonts,
    text_width,
)

KAZAKH_LETTERS = "ӘҒҚҢӨҰҮҺІәғқңөұүһі"
RUSSIAN_LETTERS = "ЁЙЩЪЫЬЭЮЯёйщъыьэюя"
PUNCTUATION = "«»№·—"


def test_register_fonts_is_idempotent() -> None:
    register_fonts()
    register_fonts()
    registered = pdfmetrics.getRegisteredFontNames()
    for name in FONT_FILES:
        assert name in registered


def test_every_font_covers_russian_and_kazakh() -> None:
    for name, filename in FONT_FILES.items():
        font = TTFont(name, str(FONT_DIR / filename))
        missing = [
            char
            for char in KAZAKH_LETTERS + RUSSIAN_LETTERS + PUNCTUATION
            if ord(char) not in font.face.charToGlyph
        ]
        assert not missing, f"в {filename} нет символов: {''.join(missing)}"


def test_licence_is_shipped_with_the_fonts() -> None:
    assert (FONT_DIR / "LICENSE-DejaVu.txt").is_file()


def test_number_font_digits_are_monospaced() -> None:
    # Цифры одинаковой ширины: любой номер одной длины занимает одно и то же место.
    assert text_width("111", NUMBER, 100) == text_width("300", NUMBER, 100)


def test_number_font_is_narrower_than_the_text_font() -> None:
    assert text_width("300", NUMBER, 100) < text_width("300", SANS, 100)


def test_cap_height_scales_with_size() -> None:
    assert cap_height(NUMBER, 100) == 2 * cap_height(NUMBER, 50)
    assert 0.5 < cap_height(NUMBER, 100) / 100 < 0.9
