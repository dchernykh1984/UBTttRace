"""Фон печатного листа.

По умолчанию фон рисуется кодом в цветах команды: кремовый лист, оранжевые
полосы сверху и снизу с чёрной отбивкой — как вставки на джерси, — двойная
рамка и бледный логотип водяным знаком. Вектор печатается чётко на любом
принтере и ничего не весит.

Если хочется другой вид, фон можно подменить картинкой: см. `resolve_image`.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from reportlab.lib.units import mm
from reportlab.pdfgen.canvas import Canvas

from .brand import INK, ORANGE, PAPER, draw_logo

BACKGROUND_DIR = Path(__file__).parent / "assets" / "backgrounds"
BACKGROUND_NAMES = ("certificate.png", "certificate.jpg", "certificate.jpeg")


@dataclass(frozen=True, slots=True)
class BackgroundStyle:
    """Пропорции фирменного фона."""

    safe_margin: float = 6 * mm
    """Отступ от края листа: офисный принтер до самого края не печатает,
    и фон, уходящий под обрез, вылезает белой каймой."""

    band_height: float = 9 * mm
    """Оранжевая полоса по верхнему и нижнему краю."""

    band_rule: float = 1.2 * mm
    """Чёрная отбивка под полосой."""

    frame_margin: float = 21 * mm
    """Рамка идёт внутри полос: она должна начинаться уже за отбивкой,
    иначе её горизонтальные стороны просто прячутся под чёрной линией."""

    frame_inset: float = 2.5 * mm
    watermark_size: float = 90 * mm
    watermark_alpha: float = 0.07
    """Логотип должен угадываться, но не мешать читать текст."""


def draw_image_background(canvas: Canvas, width: float, height: float, image: Path) -> None:
    """Растянуть картинку на весь лист."""
    canvas.drawImage(str(image), 0, 0, width=width, height=height, mask="auto")


def draw_branded_background(
    canvas: Canvas,
    width: float,
    height: float,
    style: BackgroundStyle | None = None,
) -> None:
    """Нарисовать фирменный фон командными цветами."""
    style = style or BackgroundStyle()

    left = style.safe_margin
    bottom = style.safe_margin
    inner_width = width - 2 * style.safe_margin
    inner_height = height - 2 * style.safe_margin

    canvas.saveState()
    canvas.setFillColor(PAPER)
    canvas.rect(left, bottom, inner_width, inner_height, stroke=0, fill=1)

    top_band = bottom + inner_height - style.band_height
    for band_bottom, rule_bottom in (
        (top_band, top_band - style.band_rule),
        (bottom, bottom + style.band_height),
    ):
        canvas.setFillColor(ORANGE)
        canvas.rect(left, band_bottom, inner_width, style.band_height, stroke=0, fill=1)
        canvas.setFillColor(INK)
        canvas.rect(left, rule_bottom, inner_width, style.band_rule, stroke=0, fill=1)

    canvas.setStrokeColor(INK)
    canvas.setLineWidth(1.1)
    margin = style.frame_margin
    canvas.rect(margin, margin, width - 2 * margin, height - 2 * margin, stroke=1, fill=0)

    canvas.setStrokeColor(ORANGE)
    canvas.setLineWidth(0.5)
    inset = margin + style.frame_inset
    canvas.rect(inset, inset, width - 2 * inset, height - 2 * inset, stroke=1, fill=0)
    canvas.restoreState()

    canvas.saveState()
    canvas.setFillAlpha(style.watermark_alpha)
    draw_logo(canvas, width / 2, height / 2, style.watermark_size)
    canvas.restoreState()


def draw_background(
    canvas: Canvas,
    width: float,
    height: float,
    image: Path | None = None,
    style: BackgroundStyle | None = None,
) -> None:
    """Фон листа: картинка, если она задана, иначе фирменный фон кодом."""
    if image is not None:
        draw_image_background(canvas, width, height, image)
        return
    draw_branded_background(canvas, width, height, style)


def resolve_image(explicit: Path | None = None) -> Path | None:
    """Какую картинку подложить под лист.

    Либо ту, что назвали явно, либо ту, что лежит в `assets/backgrounds`.
    Если ни одной нет — None, и фон нарисуется кодом.
    """
    if explicit is not None:
        if not explicit.is_file():
            raise ValueError(f"нет файла фона: {explicit}")
        return explicit

    for name in BACKGROUND_NAMES:
        candidate = BACKGROUND_DIR / name
        if candidate.is_file():
            return candidate
    return None
