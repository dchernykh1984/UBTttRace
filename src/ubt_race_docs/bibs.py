"""Стартовые номера на подседельный штырь.

Лист A4 кладётся горизонтально и разрезается вдоль пополам — получаются две
полоски 297×105 мм, по одному номеру на полоску. Полоска серединой оборачивается
вокруг подседельной трубы, хвосты склеиваются между собой чистыми сторонами.
Номер печатается на каждом хвосте, поэтому читается и слева, и справа.

Каждая половина полоски обходит трубу на половину её периметра, и вдвоём они
замыкают полный оборот — только так номер держится и не сползает. Для трубы
диаметром 34 мм это 53 мм бумаги с каждой стороны от сгиба, у аэропрофилей
бывает и больше, поэтому запас взят с походом. Цифры начинаются уже за этой
зоной и сильно растянуты по вертикали: ширину ограничивает длина хвоста,
а высоту полоски (105 мм) грех не использовать.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import pi
from pathlib import Path

from reportlab.lib.units import mm
from reportlab.pdfgen.canvas import Canvas

from .brand import ORANGE, draw_logo
from .draw import centred_string, dashed_line, qr_code, stretched_string
from .fonts import NUMBER, SANS_BOLD, cap_height, register_fonts, text_width
from .race import RACE

FIRST_BIB = 1
LAST_BIB = 300


@dataclass(frozen=True, slots=True)
class BibLayout:
    """Геометрия полоски с номером."""

    page_width: float = 297 * mm
    page_height: float = 210 * mm
    wrap_allowance: float = 55 * mm
    """Половина периметра подседельной трубы: столько съедает оборот вокруг неё."""

    outer_margin: float = 8 * mm
    top_margin: float = 7 * mm
    bottom_margin: float = 7 * mm
    qr_size: float = 20 * mm
    """QR ведёт на страницу гонки — с него удобно смотреть протокол."""

    footer_gap: float = 3 * mm
    wordmark_size: float = 11
    wordmark_tracking: float = 2.5

    logo_size: float = 24 * mm
    """Логотип на сгибе: он ляжет прямо на подседельную трубу."""

    logo_gap: float = 3 * mm

    max_stretch: float = 2.0
    """Растяжение по вертикали: оборот вокруг трубы съедает ширину, и высота —
    единственный способ вернуть цифрам размер. Больше — цифры выглядят
    неестественно вытянутыми."""

    @property
    def strip_height(self) -> float:
        return self.page_height / 2

    @property
    def center_x(self) -> float:
        return self.page_width / 2

    @property
    def number_width(self) -> float:
        """Ширина хвоста, в которую должен уместиться номер."""
        return self.center_x - self.wrap_allowance - self.outer_margin

    def wraps_tube_of_diameter(self, diameter: float) -> bool:
        """Хватает ли запаса, чтобы обойти круглую трубу такого диаметра."""
        return self.wrap_allowance >= pi * diameter / 2

    @property
    def band_bottom(self) -> float:
        """Низ зоны под цифры, от низа полоски: под ними идут QR и марка."""
        return self.bottom_margin + self.qr_size + self.footer_gap

    @property
    def band_top(self) -> float:
        """Верх зоны под цифры, от низа полоски."""
        return self.strip_height - self.top_margin

    @property
    def band_height(self) -> float:
        return self.band_top - self.band_bottom


def number_font_size(layout: BibLayout, digits: int) -> float:
    """Кегль, при котором самый широкий номер занимает всю ширину хвоста."""
    if digits < 1:
        raise ValueError("в номере должна быть хотя бы одна цифра")
    reference = "8" * digits
    return layout.number_width / text_width(reference, NUMBER, 1)


def number_stretch(layout: BibLayout, font_size: float) -> float:
    """Во сколько раз растянуть цифры по вертикали, чтобы заполнить полоску."""
    return min(layout.max_stretch, layout.band_height / cap_height(NUMBER, font_size))


def draw_strip(
    canvas: Canvas,
    number: int,
    strip_bottom: float,
    layout: BibLayout,
    font_size: float,
    stretch: float,
) -> None:
    """Нарисовать одну полоску: номер на обоих хвостах и линия сгиба."""
    text = str(number)
    digit_height = cap_height(NUMBER, font_size) * stretch
    baseline = strip_bottom + layout.band_bottom + (layout.band_height - digit_height) / 2

    left_tail = layout.outer_margin
    right_tail = layout.page_width - layout.outer_margin - layout.number_width

    for tail_left in (left_tail, right_tail):
        center = tail_left + layout.number_width / 2
        stretched_string(canvas, center, baseline, text, NUMBER, font_size, stretch)
        draw_tail_footer(canvas, tail_left, strip_bottom, layout)

    draw_fold(canvas, strip_bottom, layout)


def draw_tail_footer(
    canvas: Canvas,
    tail_left: float,
    strip_bottom: float,
    layout: BibLayout,
) -> None:
    """Подвал хвоста: QR у дальнего от сгиба края и марка гонки рядом с ним."""
    far_side_is_right = tail_left > layout.center_x
    wordmark_width = layout.number_width - layout.qr_size - layout.footer_gap

    if far_side_is_right:
        qr_x = tail_left + layout.number_width - layout.qr_size
        wordmark_left = tail_left
    else:
        qr_x = tail_left
        wordmark_left = tail_left + layout.qr_size + layout.footer_gap

    qr_code(canvas, qr_x, strip_bottom + layout.bottom_margin, layout.qr_size, RACE.url)
    centred_string(
        canvas,
        wordmark_left + wordmark_width / 2,
        strip_bottom + layout.bottom_margin + (layout.qr_size - layout.wordmark_size) / 2,
        RACE.short_title,
        SANS_BOLD,
        layout.wordmark_size,
        ORANGE,
        tracking=layout.wordmark_tracking,
    )


def draw_fold(canvas: Canvas, strip_bottom: float, layout: BibLayout) -> None:
    """Линия сгиба с логотипом посередине — он окажется спереди на трубе."""
    middle = strip_bottom + layout.strip_height / 2
    half = layout.logo_size / 2 + layout.logo_gap
    for start, end in (
        (strip_bottom + layout.bottom_margin, middle - half),
        (middle + half, strip_bottom + layout.strip_height - layout.top_margin),
    ):
        dashed_line(canvas, layout.center_x, start, layout.center_x, end, dash=(3, 3))
    draw_logo(canvas, layout.center_x, middle, layout.logo_size)


def draw_cut_line(canvas: Canvas, layout: BibLayout) -> None:
    """Линия, по которой лист режется вдоль на две полоски."""
    y = layout.page_height / 2
    dashed_line(canvas, 0, y, layout.page_width, y, dash=(6, 4), width=0.6)


def build_bibs(
    output: Path,
    first: int = FIRST_BIB,
    last: int = LAST_BIB,
    layout: BibLayout | None = None,
) -> Path:
    """Собрать PDF со стартовыми номерами `first`..`last` включительно."""
    if first < 1:
        raise ValueError(f"номера начинаются с 1, получено {first}")
    if last < first:
        raise ValueError(f"последний номер {last} меньше первого {first}")

    register_fonts()
    layout = layout or BibLayout()
    font_size = number_font_size(layout, len(str(last)))
    stretch = number_stretch(layout, font_size)

    output.parent.mkdir(parents=True, exist_ok=True)
    canvas = Canvas(str(output), pagesize=(layout.page_width, layout.page_height))
    canvas.setTitle(f"Стартовые номера {first}–{last} · {RACE.short_title}")
    canvas.setAuthor(RACE.organizer)
    canvas.setSubject(RACE.title.ru)

    numbers = list(range(first, last + 1))
    for index in range(0, len(numbers), 2):
        draw_cut_line(canvas, layout)
        draw_strip(canvas, numbers[index], layout.strip_height, layout, font_size, stretch)
        if index + 1 < len(numbers):
            draw_strip(canvas, numbers[index + 1], 0, layout, font_size, stretch)
        canvas.showPage()

    canvas.save()
    return output
