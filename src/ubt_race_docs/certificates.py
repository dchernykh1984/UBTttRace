"""Грамоты призёрам.

Каждая грамота — отдельный лист A4. Зачёт и место напечатаны заранее: по
положению награждается первая тройка в абсолюте отдельно у мужчин и у женщин
и первая тройка в каждой возрастной группе. От руки на месте вписываются
фамилия, имя и результат. Плюс запасные бланки, где не заполнено вообще
ничего — на случай, если зачёт или место придётся написать другие.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from reportlab.lib.units import mm
from reportlab.pdfgen.canvas import Canvas

from .background import draw_background, resolve_image
from .brand import INK, MUTED, ORANGE, draw_giant
from .draw import captioned_fill_line, centred_block, centred_string, fill_line
from .fonts import SANS, SANS_BOLD, TITLE, fit_size, register_fonts
from .race import AWARDED_PLACES, RACE, AwardGroup, Bilingual, award_groups, place_title

SPARE_CERTIFICATES = 3

HEADING = "ГРАМОТА"
AWARDED_TO = Bilingual("Награждается", "Марапатталады")
CATEGORY_CAPTION = Bilingual("Зачёт", "Сынып")
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
    field_width: float = 130 * mm

    heading_y: float = 45 * mm
    rule_y: float = 53 * mm
    rule_width: float = 70 * mm
    title_y: float = 68 * mm
    title_size: float = 10.5
    title_width: float = 160 * mm
    """Сколько места между сторонами рамки остаётся названию гонки."""
    details_y: float = 85 * mm
    category_y: float = 102 * mm
    category_leading: float = 17
    place_y: float = 122 * mm
    awarded_y: float = 141 * mm
    surname_y: float = 163 * mm
    name_y: float = 185 * mm
    result_y: float = 207 * mm
    signature_y: float = 243 * mm
    signature_width: float = 60 * mm
    giant_y: float = 257 * mm
    giant_width: float = 34 * mm
    footer_y: float = 266 * mm

    def top(self, offset: float) -> float:
        """Перевести отступ от верха листа в координату reportlab."""
        return self.page_height - offset


def draw_certificate(
    canvas: Canvas,
    layout: CertificateLayout,
    group: AwardGroup | None = None,
    place: int | None = None,
    background: Path | None = None,
) -> None:
    """Нарисовать одну грамоту. Пустые `group` и `place` — запасной бланк."""
    center = layout.page_width / 2
    draw_background(canvas, layout.page_width, layout.page_height, image=background)

    centred_string(canvas, center, layout.top(layout.heading_y), HEADING, TITLE, 44, INK)
    fill_line(
        canvas,
        center - layout.rule_width / 2,
        layout.top(layout.rule_y),
        layout.rule_width,
        line_width=1.4,
        colour=ORANGE,
    )
    # Название гонки живёт в race.py и может смениться: подбираем кегль,
    # чтобы длинная строка не вылезла за рамку.
    title_size = min(
        fit_size(line, SANS, layout.title_width, layout.title_size, min_size=8)
        for line in RACE.title.lines()
    )
    y = layout.top(layout.title_y)
    for line in RACE.title.lines():
        centred_string(canvas, center, y, line, SANS, title_size, INK)
        y -= layout.title_size + 3.5
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
        MUTED,
    )

    if group is None:
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
        # Названия зачётов длинные («Мужчины, 1970 г.р. и старше»), поэтому
        # русская и казахская строки идут одна под другой, а не через точку.
        centred_block(
            canvas,
            center,
            layout.top(layout.category_y),
            group.title.lines(),
            SANS_BOLD,
            14,
            layout.category_leading,
            INK,
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

    # Имя стоит над чертой — там же, где от руки вписывают фамилию и результат,
    # а под чертой остаётся подпись должности.
    signature = layout.top(layout.signature_y)
    centred_string(canvas, center, signature + 5, RACE.chief_referee, SANS, 12.5, INK)
    fill_line(canvas, center - layout.signature_width / 2, signature, layout.signature_width)
    centred_string(canvas, center, signature - 12, REFEREE_CAPTION.one_line(), SANS, 9, MUTED)
    # Логотип партнёра гонки — над подписью организатора, как на джерси.
    draw_giant(canvas, center, layout.top(layout.giant_y), layout.giant_width)
    centred_block(
        canvas,
        center,
        layout.top(layout.footer_y),
        (RACE.organizer, RACE.site_url),
        SANS,
        8.5,
        11,
        MUTED,
    )


def build_certificates(
    output: Path,
    spare: int = SPARE_CERTIFICATES,
    layout: CertificateLayout | None = None,
    background: Path | None = None,
) -> Path:
    """Собрать PDF: заполненные грамоты для призёров плюс `spare` пустых бланков.

    `background` — своя картинка на весь лист вместо нарисованного фона.
    """
    if spare < 0:
        raise ValueError(f"запасных бланков не может быть меньше нуля, получено {spare}")

    register_fonts()
    layout = layout or CertificateLayout()
    image = resolve_image(background)

    output.parent.mkdir(parents=True, exist_ok=True)
    canvas = Canvas(str(output), pagesize=(layout.page_width, layout.page_height))
    canvas.setTitle(f"Грамоты · {RACE.short_title}")
    canvas.setAuthor(RACE.organizer)
    canvas.setSubject(RACE.title.ru)

    for group in award_groups():
        for place in AWARDED_PLACES:
            draw_certificate(canvas, layout, group, place, background=image)
            canvas.showPage()

    for _ in range(spare):
        draw_certificate(canvas, layout, background=image)
        canvas.showPage()

    canvas.save()
    return output
