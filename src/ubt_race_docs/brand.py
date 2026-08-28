"""Фирменный стиль команды: цвета и логотип.

Цвета сняты с логотипа Universal Bicycle Team и с командной формы —
оранжевое джерси с чёрными вставками. Всё, что раскрашивает документы,
берёт цвета отсюда, чтобы номера, грамоты и расписки выглядели одинаково.
"""

from __future__ import annotations

from pathlib import Path

from reportlab.lib import colors
from reportlab.pdfgen.canvas import Canvas

LOGO_PATH = Path(__file__).parent / "assets" / "images" / "ubt-logo.png"
GIANT_LOGO_PATH = Path(__file__).parent / "assets" / "images" / "giant-logo.png"

GIANT_ASPECT = 308 / 1600
"""Высота логотипа Giant относительно его длины — файл 1600×308."""

ORANGE = colors.HexColor("#F08020")
"""Джерси команды и подпись на логотипе."""

BLUE = colors.HexColor("#2030B0")
"""Велосипедист на логотипе."""

GREEN = colors.HexColor("#33B012")
"""Третий цвет логотипа."""

INK = colors.HexColor("#1D1D1B")
"""Чёрные вставки формы — им же набран текст."""

PAPER = colors.HexColor("#FDFBF6")
"""Кремовый тон листа: теплее белого, но не отвлекает."""

MUTED = colors.HexColor("#8A8A88")
"""Мелкие подписи."""


def draw_logo(canvas: Canvas, x_center: float, y_center: float, size: float) -> None:
    """Нарисовать логотип квадратом `size`, отцентрированным по точке."""
    canvas.drawImage(
        str(LOGO_PATH),
        x_center - size / 2,
        y_center - size / 2,
        width=size,
        height=size,
        mask="auto",
    )


def draw_giant(
    canvas: Canvas,
    x_center: float,
    y_center: float,
    width: float,
    angle: float = 0.0,
) -> None:
    """Логотип партнёра, отцентрированный по точке и повёрнутый на `angle`."""
    height = width * GIANT_ASPECT
    canvas.saveState()
    canvas.translate(x_center, y_center)
    canvas.rotate(angle)
    canvas.drawImage(
        str(GIANT_LOGO_PATH),
        -width / 2,
        -height / 2,
        width=width,
        height=height,
        mask="auto",
    )
    canvas.restoreState()
