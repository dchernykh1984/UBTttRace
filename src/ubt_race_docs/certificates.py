"""Грамоты призёрам.

Каждая грамота — отдельный лист A4. Категория и место напечатаны заранее
(по положению награждается первая тройка у мужчин и у женщин), от руки на месте
вписываются фамилия, имя и результат. Плюс запасные бланки, где не заполнено
вообще ничего — на случай, если категорию или место придётся написать другие.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.pdfgen.canvas import Canvas

from .draw import GREY, captioned_fill_line, centred_block, centred_string, fill_line
from .fonts import SANS, SANS_BOLD, TITLE, register_fonts
from .race import AWARDED_PLACES, CATEGORIES, RACE, Bilingual, Category, place_title

SPARE_CERTIFICATES = 2

HEADING = "ГРАМОТА"
AWARDED_TO = Bilingual("Награждается", "Марапатталады")
CATEGORY_CAPTION = Bilingual("Категория", "Санаты")
PLACE_CAPTION = Bilingual("Место", "Орны")
SURNAME_CAPTION = Bilingual("Фамилия", "Тегі")
NAME_CAPTION = Bilingual("Имя", "Аты")
RESULT_CAPTION = Bilingual("Результат", "Нәтижесі")
REFEREE_CAPTION = Bilingual("Главный судья", "Бас төреші")


@dataclass(frozen=True, slots=True)
class CertificateLayout:
    """Вертикальная раскладка грамоты, все отступы — от верха листа."""

    page_width: float = 210 * mm
    page_height: float = 297 * mm
    border_margin: float = 12 * mm
    field_width: float = 130 * mm

    heading_y: float = 45 * mm
    rule_y: float = 53 * mm
    rule_width: float = 70 * mm
    title_y: float = 68 * mm
    details_y: float = 85 * mm
    category_y: float = 104 * mm
    place_y: float = 122 * mm
    awarded_y: float = 141 * mm
    surname_y: float = 163 * mm
    name_y: float = 185 * mm
    result_y: float = 207 * mm
    signature_y: float = 243 * mm
    footer_y: float = 272 * mm

    def top(self, offset: float) -> float:
        """Перевести отступ от верха листа в координату reportlab."""
        return self.page_height - offset


def draw_border(canvas: Canvas, layout: CertificateLayout) -> None:
    """Двойная рамка по краю листа."""
    canvas.saveState()
    canvas.setStrokeColor(colors.black)
    canvas.setLineWidth(1.6)
    margin = layout.border_margin
    canvas.rect(
        margin,
        margin,
        layout.page_width - 2 * margin,
        layout.page_height - 2 * margin,
    )
    canvas.setLineWidth(0.5)
    inner = margin + 3 * mm
    canvas.rect(
        inner,
        inner,
        layout.page_width - 2 * inner,
        layout.page_height - 2 * inner,
    )
    canvas.restoreState()


def draw_certificate(
    canvas: Canvas,
    layout: CertificateLayout,
    category: Category | None = None,
    place: int | None = None,
) -> None:
    """Нарисовать одну грамоту. Пустые `category` и `place` — запасной бланк."""
    center = layout.page_width / 2
    draw_border(canvas, layout)

    centred_string(canvas, center, layout.top(layout.heading_y), HEADING, TITLE, 44)
    fill_line(
        canvas,
        center - layout.rule_width / 2,
        layout.top(layout.rule_y),
        layout.rule_width,
        line_width=1.2,
    )
    centred_block(canvas, center, layout.top(layout.title_y), RACE.title.lines(), SANS, 10.5, 14)
    centred_block(
        canvas,
        center,
        layout.top(layout.details_y),
        (
            f"{RACE.date.ru} · {RACE.place.ru} · {RACE.distance.ru}",
            f"{RACE.date.kk} · {RACE.place.kk} · {RACE.distance.kk}",
        ),
        SANS,
        9,
        12,
        GREY,
    )

    if category is None:
        captioned_fill_line(
            canvas,
            center,
            layout.top(layout.category_y),
            layout.field_width,
            CATEGORY_CAPTION.one_line(),
            SANS,
            9,
        )
    else:
        centred_string(
            canvas, center, layout.top(layout.category_y), category.name.one_line(), SANS_BOLD, 17
        )

    if place is None:
        captioned_fill_line(
            canvas,
            center,
            layout.top(layout.place_y),
            layout.field_width,
            PLACE_CAPTION.one_line(),
            SANS,
            9,
        )
    else:
        centred_string(
            canvas, center, layout.top(layout.place_y), place_title(place).one_line(), SANS_BOLD, 26
        )

    centred_string(canvas, center, layout.top(layout.awarded_y), AWARDED_TO.one_line(), SANS, 13)

    for offset, caption in (
        (layout.surname_y, SURNAME_CAPTION),
        (layout.name_y, NAME_CAPTION),
        (layout.result_y, RESULT_CAPTION),
    ):
        captioned_fill_line(
            canvas,
            center,
            layout.top(offset),
            layout.field_width,
            caption.one_line(),
            SANS,
            9,
        )

    captioned_fill_line(
        canvas,
        center,
        layout.top(layout.signature_y),
        80 * mm,
        REFEREE_CAPTION.one_line(),
        SANS,
        9,
    )
    centred_block(
        canvas,
        center,
        layout.top(layout.footer_y),
        (RACE.organizer, RACE.url),
        SANS,
        8.5,
        11,
        GREY,
    )


def build_certificates(
    output: Path,
    spare: int = SPARE_CERTIFICATES,
    layout: CertificateLayout | None = None,
) -> Path:
    """Собрать PDF: заполненные грамоты для призёров плюс `spare` пустых бланков."""
    if spare < 0:
        raise ValueError(f"запасных бланков не может быть меньше нуля, получено {spare}")

    register_fonts()
    layout = layout or CertificateLayout()

    output.parent.mkdir(parents=True, exist_ok=True)
    canvas = Canvas(str(output), pagesize=(layout.page_width, layout.page_height))
    canvas.setTitle(f"Грамоты · {RACE.short_title}")
    canvas.setAuthor(RACE.organizer)
    canvas.setSubject(RACE.title.ru)

    for category in CATEGORIES:
        for place in AWARDED_PLACES:
            draw_certificate(canvas, layout, category, place)
            canvas.showPage()

    for _ in range(spare):
        draw_certificate(canvas, layout)
        canvas.showPage()

    canvas.save()
    return output
