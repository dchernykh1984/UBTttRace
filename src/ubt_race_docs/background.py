"""Фон печатного листа.

По умолчанию фон рисуется кодом в цветах команды: тёплый тон бумаги, двойная
рамка с оранжевыми уголками и бледный логотип водяным знаком. Вектор печатается
чётко на любом принтере и ничего не весит.

Заливка идёт на весь лист, а рисованного «под обрез» тут намеренно нет: офисный
принтер до края не печатает, и любая цветная плашка у границы вылезла бы белой
каймой. Тон бумаги от белого почти не отличается, поэтому его край незаметен.

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

    frame_margin: float = 14 * mm
    """Отступ внешней рамки от края листа."""

    frame_inset: float = 3 * mm
    """Насколько внутренняя рамка отступает от внешней."""

    corner_length: float = 34 * mm
    """Длина оранжевого уголка вдоль каждой стороны."""

    corner_width: float = 2.4
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

    canvas.saveState()
    canvas.setFillColor(PAPER)
    canvas.rect(0, 0, width, height, stroke=0, fill=1)

    canvas.setStrokeColor(INK)
    canvas.setLineWidth(1.1)
    margin = style.frame_margin
    canvas.rect(margin, margin, width - 2 * margin, height - 2 * margin, stroke=1, fill=0)

    inset = margin + style.frame_inset
    canvas.setStrokeColor(ORANGE)
    canvas.setLineWidth(0.6)
    canvas.rect(inset, inset, width - 2 * inset, height - 2 * inset, stroke=1, fill=0)

    draw_corners(canvas, width, height, style)
    canvas.restoreState()

    canvas.saveState()
    canvas.setFillAlpha(style.watermark_alpha)
    draw_logo(canvas, width / 2, height / 2, style.watermark_size)
    canvas.restoreState()


def draw_corners(
    canvas: Canvas,
    width: float,
    height: float,
    style: BackgroundStyle,
) -> None:
    """Оранжевые уголки на внутренней рамке — от них лист выглядит наградным."""
    inset = style.frame_margin + style.frame_inset
    left, right = inset, width - inset
    bottom, top = inset, height - inset
    reach = style.corner_length

    canvas.saveState()
    canvas.setStrokeColor(ORANGE)
    canvas.setLineWidth(style.corner_width)
    canvas.setLineCap(0)
    for x, x_step in ((left, 1), (right, -1)):
        for y, y_step in ((bottom, 1), (top, -1)):
            canvas.line(x, y, x + x_step * reach, y)
            canvas.line(x, y, x, y + y_step * reach)
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
