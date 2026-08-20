"""Мелкие примитивы рисования поверх reportlab.

Всё, что нужно нескольким документам сразу: центрированный текст, растянутые по
высоте цифры, пунктирные линии реза и линейки для заполнения от руки.
"""

from __future__ import annotations

from reportlab.lib import colors
from reportlab.pdfgen.canvas import Canvas

from .fonts import cap_height, register_fonts, text_width

GREY = colors.Color(0.45, 0.45, 0.45)


def centred_string(
    canvas: Canvas,
    x_center: float,
    y: float,
    text: str,
    font: str,
    size: float,
    colour: colors.Color | None = None,
) -> None:
    """Нарисовать строку, отцентрированную по `x_center`, базовой линией на `y`."""
    register_fonts()
    canvas.saveState()
    canvas.setFont(font, size)
    if colour is not None:
        canvas.setFillColor(colour)
    canvas.drawString(x_center - text_width(text, font, size) / 2, y, text)
    canvas.restoreState()


def centred_block(
    canvas: Canvas,
    x_center: float,
    y_top: float,
    lines: tuple[str, ...],
    font: str,
    size: float,
    leading: float,
    colour: colors.Color | None = None,
) -> float:
    """Нарисовать несколько центрированных строк сверху вниз.

    Возвращает базовую линию последней строки.
    """
    y = y_top
    for line in lines:
        centred_string(canvas, x_center, y, line, font, size, colour)
        y -= leading
    return y + leading


def stretched_string(
    canvas: Canvas,
    x_center: float,
    y_baseline: float,
    text: str,
    font: str,
    size: float,
    stretch: float,
) -> None:
    """Нарисовать строку, растянутую по вертикали в `stretch` раз.

    Так цифры номера занимают всю высоту полоски, не становясь шире: ширина
    ограничена длиной хвоста, который остаётся за подседельным штырём.
    """
    register_fonts()
    canvas.saveState()
    canvas.translate(x_center - text_width(text, font, size) / 2, y_baseline)
    canvas.scale(1.0, stretch)
    canvas.setFont(font, size)
    canvas.drawString(0, 0, text)
    canvas.restoreState()


def stretched_height(font: str, size: float, stretch: float) -> float:
    """Высота цифр, нарисованных `stretched_string`."""
    return cap_height(font, size) * stretch


def dashed_line(
    canvas: Canvas,
    x1: float,
    y1: float,
    x2: float,
    y2: float,
    dash: tuple[float, float] = (4, 4),
    width: float = 0.5,
    colour: colors.Color = GREY,
) -> None:
    """Пунктир — линия реза или сгиба."""
    canvas.saveState()
    canvas.setDash(list(dash))
    canvas.setLineWidth(width)
    canvas.setStrokeColor(colour)
    canvas.line(x1, y1, x2, y2)
    canvas.restoreState()


def rotated_string(
    canvas: Canvas,
    x: float,
    y: float,
    text: str,
    font: str,
    size: float,
    angle: float = 90,
    colour: colors.Color = GREY,
) -> None:
    """Строка, повёрнутая на `angle` градусов вокруг точки (x, y)."""
    register_fonts()
    canvas.saveState()
    canvas.translate(x, y)
    canvas.rotate(angle)
    canvas.setFont(font, size)
    canvas.setFillColor(colour)
    canvas.drawString(0, 0, text)
    canvas.restoreState()


def fill_line(
    canvas: Canvas,
    x: float,
    y: float,
    width: float,
    line_width: float = 0.7,
    colour: colors.Color = colors.black,
) -> None:
    """Линейка, по которой пишут от руки."""
    canvas.saveState()
    canvas.setLineWidth(line_width)
    canvas.setStrokeColor(colour)
    canvas.setDash([])
    canvas.line(x, y, x + width, y)
    canvas.restoreState()


def labelled_fill_line(
    canvas: Canvas,
    x: float,
    y: float,
    width: float,
    label: str,
    font: str,
    size: float,
    gap: float = 6,
) -> None:
    """Подпись слева и линейка для заполнения справа от неё."""
    register_fonts()
    canvas.saveState()
    canvas.setFont(font, size)
    canvas.setFillColor(colors.black)
    canvas.drawString(x, y + gap * 0.35, label)
    canvas.restoreState()
    start = x + text_width(label, font, size) + gap
    fill_line(canvas, start, y, max(width - (start - x), 0))


def captioned_fill_line(
    canvas: Canvas,
    x_center: float,
    y: float,
    width: float,
    caption: str,
    font: str,
    size: float,
    gap: float = 5,
) -> None:
    """Линейка для заполнения с мелкой подписью под ней."""
    fill_line(canvas, x_center - width / 2, y, width)
    centred_string(canvas, x_center, y - gap - size * 0.8, caption, font, size, GREY)
