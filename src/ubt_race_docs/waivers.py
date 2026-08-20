"""Расписки об ответственности.

Два отдельных бланка: для совершеннолетнего участника и для законного
представителя несовершеннолетнего. Каждый — один лист A4: шапка, поля под
данные, обязательства в две колонки (слева по-русски, справа по-казахски) и
место для подписи. Организаторы печатают пачку и выдают на регистрации.

Это шаблон бланка, а не юридическая консультация: перед печатью текст стоит
показать юристу.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfgen.canvas import Canvas
from reportlab.platypus import Paragraph

from .draw import GREY, centred_string, fill_line
from .fonts import SANS, SANS_BOLD, fit_size, register_fonts
from .race import RACE, Bilingual


@dataclass(frozen=True, slots=True)
class Field:
    """Поле для заполнения от руки."""

    label: Bilingual
    weight: float = 1.0


@dataclass(frozen=True, slots=True)
class FieldBlock:
    """Блок полей с необязательным заголовком."""

    heading: Bilingual | None
    rows: tuple[tuple[Field, ...], ...]


@dataclass(frozen=True, slots=True)
class WaiverForm:
    """Содержимое одного бланка расписки."""

    slug: str
    title: Bilingual
    intro: Bilingual
    blocks: tuple[FieldBlock, ...]
    statements: tuple[Bilingual, ...]
    footer_note: Bilingual


@dataclass(frozen=True, slots=True)
class WaiverLayout:
    """Геометрия бланка."""

    page_width: float = 210 * mm
    page_height: float = 297 * mm
    margin: float = 15 * mm
    column_gutter: float = 6 * mm
    title_size: float = 13
    meta_size: float = 8
    intro_size: float = 9
    label_size: float = 8
    statement_size: float = 8
    statement_leading: float = 10
    field_step: float = 11 * mm

    @property
    def content_width(self) -> float:
        return self.page_width - 2 * self.margin

    @property
    def column_width(self) -> float:
        return (self.content_width - self.column_gutter) / 2


PERSON_ROWS: tuple[tuple[Field, ...], ...] = (
    (Field(Bilingual("Фамилия, имя, отчество", "Тегі, аты, әкесінің аты")),),
    (
        Field(Bilingual("Дата рождения", "Туған күні")),
        Field(Bilingual("Телефон", "Телефоны")),
        Field(Bilingual("Стартовый номер", "Старттық нөмірі")),
    ),
)

EMERGENCY_BLOCK = FieldBlock(
    heading=Bilingual(
        "Кому звонить в экстренном случае", "Төтенше жағдайда кімге қоңырау шалу керек"
    ),
    rows=(
        (
            Field(Bilingual("Фамилия, имя", "Тегі, аты"), weight=1.6),
            Field(Bilingual("Телефон", "Телефоны")),
        ),
    ),
)

ADULT_FORM = WaiverForm(
    slug="adult",
    title=Bilingual(
        "РАСПИСКА ОБ ОТВЕТСТВЕННОСТИ УЧАСТНИКА",
        "ҚАТЫСУШЫНЫҢ ЖАУАПКЕРШІЛІГІ ТУРАЛЫ ҚОЛХАТ",
    ),
    intro=Bilingual(
        "Я, участник мероприятия, настоящим подтверждаю:",
        "Мен, іс-шараға қатысушы, осымен растаймын:",
    ),
    blocks=(
        FieldBlock(heading=Bilingual("Участник", "Қатысушы"), rows=PERSON_ROWS),
        EMERGENCY_BLOCK,
    ),
    statements=(
        Bilingual(
            "Я ознакомлен(а) с положением мероприятия, согласен(на) с ним и обязуюсь его "
            "соблюдать.",
            "Мен іс-шара ережесімен таныстым, онымен келісемін және оны сақтауға міндеттенемін.",
        ),
        Bilingual(
            "Мероприятие проходит по дороге общего пользования, движение по ней не перекрывается. "
            "Я обязуюсь соблюдать Правила дорожного движения Республики Казахстан и понимаю, "
            "что за их нарушение отвечаю сам(а).",
            "Іс-шара жалпыға ортақ жолда өтеді, қозғалыс жабылмайды. Мен Қазақстан Республикасының "
            "жол қозғалысы ережелерін сақтауға міндеттенемін және оларды бұзғаным үшін өзім жауап "
            "беретінімді түсінемін.",
        ),
        Bilingual(
            "Состояние моего здоровья позволяет мне участвовать, медицинских противопоказаний у "
            "меня нет; "
            "оценку своего состояния я делаю сам(а).",
            "Денсаулығымның жағдайы қатысуға мүмкіндік береді, медициналық қарсы көрсетілімдерім "
            "жоқ; "
            "өз жағдайымды өзім бағалаймын.",
        ),
        Bilingual(
            "Я понимаю, что езда на велосипеде связана с риском падения, травмы, увечья и гибели, "
            "и принимаю этот риск на себя.",
            "Велосипед тебу құлау, жарақат алу, мүгедек болу және қаза болу қаупімен байланысты "
            "екенін "
            "түсінемін және бұл тәуекелді өз мойныма аламын.",
        ),
        Bilingual(
            "Я стартую на исправном велосипеде и в застёгнутом шлеме.",
            "Мен ақаусыз велосипедпен және тағылған шлеммен старт аламын.",
        ),
        Bilingual(
            "Ответственность за свою жизнь, здоровье и имущество я несу самостоятельно; претензий "
            "к организаторам не имею и обязуюсь их не предъявлять.",
            "Өз өмірім, денсаулығым және мүлкім үшін жауапкершілікті өзім көтеремін; "
            "ұйымдастырушыларға "
            "наразылығым жоқ және оларды білдірмеуге міндеттенемін.",
        ),
        Bilingual(
            "Я даю согласие на сбор и обработку моих персональных данных для проведения "
            "мероприятия "
            "и публикации протоколов, а также на фото- и видеосъёмку и её публикацию.",
            "Іс-шараны өткізу және хаттамаларды жариялау мақсатында дербес деректерімді жинауға "
            "және өңдеуге, сондай-ақ фото- және бейнетүсірілімге және оны жариялауға келісім "
            "беремін.",
        ),
    ),
    footer_note=Bilingual(
        "Расписка сдаётся организаторам при регистрации.",
        "Қолхат тіркеу кезінде ұйымдастырушыларға тапсырылады.",
    ),
)

MINOR_FORM = WaiverForm(
    slug="minor",
    title=Bilingual(
        "РАСПИСКА ЗАКОННОГО ПРЕДСТАВИТЕЛЯ НЕСОВЕРШЕННОЛЕТНЕГО УЧАСТНИКА",
        "КӘМЕЛЕТКЕ ТОЛМАҒАН ҚАТЫСУШЫНЫҢ ЗАҢДЫ ӨКІЛІНІҢ ҚОЛХАТЫ",
    ),
    intro=Bilingual(
        "Я, законный представитель несовершеннолетнего участника, настоящим подтверждаю:",
        "Мен, кәмелетке толмаған қатысушының заңды өкілі, осымен растаймын:",
    ),
    blocks=(
        FieldBlock(
            heading=Bilingual("Законный представитель", "Заңды өкіл"),
            rows=(
                (Field(Bilingual("Фамилия, имя, отчество", "Тегі, аты, әкесінің аты")),),
                (
                    Field(Bilingual("Кем приходится", "Кім болып келеді")),
                    Field(Bilingual("Документ", "Құжаты")),
                    Field(Bilingual("Телефон", "Телефоны")),
                ),
            ),
        ),
        FieldBlock(
            heading=Bilingual("Несовершеннолетний участник", "Кәмелетке толмаған қатысушы"),
            rows=PERSON_ROWS,
        ),
        EMERGENCY_BLOCK,
    ),
    statements=(
        Bilingual(
            "Я являюсь законным представителем указанного несовершеннолетнего и даю согласие "
            "на его участие в мероприятии.",
            "Мен көрсетілген кәмелетке толмаған баланың заңды өкілімін және оның іс-шараға "
            "қатысуына "
            "келісім беремін.",
        ),
        Bilingual(
            "Я ознакомлен(а) с положением мероприятия, согласен(на) с ним и обязуюсь обеспечить "
            "его соблюдение ребёнком.",
            "Мен іс-шара ережесімен таныстым, онымен келісемін және оны баланың сақтауын "
            "қамтамасыз "
            "етуге міндеттенемін.",
        ),
        Bilingual(
            "Мероприятие проходит по дороге общего пользования, движение по ней не перекрывается. "
            "Я подтверждаю, что Правила дорожного движения Республики Казахстан разрешают ребёнку "
            "самостоятельно двигаться на велосипеде по проезжей части.",
            "Іс-шара жалпыға ортақ жолда өтеді, қозғалыс жабылмайды. Қазақстан Республикасының жол "
            "қозғалысы ережелері балаға жол жүру бөлігінде велосипедпен өз бетінше жүруге рұқсат "
            "ететінін растаймын.",
        ),
        Bilingual(
            "Состояние здоровья ребёнка позволяет ему участвовать, медицинских противопоказаний "
            "нет.",
            "Баланың денсаулық жағдайы қатысуға мүмкіндік береді, медициналық қарсы көрсетілімдер "
            "жоқ.",
        ),
        Bilingual(
            "Я понимаю, что езда на велосипеде связана с риском падения, травмы, увечья и гибели, "
            "и принимаю этот риск на себя.",
            "Велосипед тебу құлау, жарақат алу, мүгедек болу және қаза болу қаупімен байланысты "
            "екенін "
            "түсінемін және бұл тәуекелді өз мойныма аламын.",
        ),
        Bilingual(
            "Ребёнок стартует на исправном велосипеде и в застёгнутом шлеме.",
            "Бала ақаусыз велосипедпен және тағылған шлеммен старт алады.",
        ),
        Bilingual(
            "Ответственность за жизнь, здоровье и имущество ребёнка несу я; претензий к "
            "организаторам "
            "не имею и обязуюсь их не предъявлять.",
            "Баланың өмірі, денсаулығы және мүлкі үшін жауапкершілікті мен көтеремін; "
            "ұйымдастырушыларға "
            "наразылығым жоқ және оларды білдірмеуге міндеттенемін.",
        ),
        Bilingual(
            "Я даю согласие на обработку персональных данных — своих и ребёнка — для проведения "
            "мероприятия и публикации протоколов, а также на фото- и видеосъёмку ребёнка "
            "и её публикацию.",
            "Іс-шараны өткізу және хаттамаларды жариялау мақсатында өзімнің және баламның дербес "
            "деректерін өңдеуге, сондай-ақ баланы фото- және бейнетүсіруге және оны жариялауға "
            "келісім беремін.",
        ),
    ),
    footer_note=Bilingual(
        "Расписка сдаётся организаторам при регистрации.",
        "Қолхат тіркеу кезінде ұйымдастырушыларға тапсырылады.",
    ),
)

FORMS: tuple[WaiverForm, ...] = (ADULT_FORM, MINOR_FORM)


def _draw_field_row(
    canvas: Canvas,
    layout: WaiverLayout,
    y: float,
    row: tuple[Field, ...],
) -> None:
    """Строка полей: линейка во всю ширину поля, двуязычная подпись под ней."""
    gutter = 6 * mm
    total_weight = sum(field.weight for field in row)
    free = layout.content_width - gutter * (len(row) - 1)
    x = layout.margin
    for field in row:
        width = free * field.weight / total_weight
        fill_line(canvas, x, y, width, line_width=0.6)
        label = field.label.one_line()
        size = fit_size(label, SANS, width, layout.label_size, min_size=6)
        canvas.saveState()
        canvas.setFont(SANS, size)
        canvas.setFillColor(GREY)
        canvas.drawString(x, y - size - 1.5, label)
        canvas.restoreState()
        x += width + gutter


def _column_flowables(
    form: WaiverForm,
    layout: WaiverLayout,
    language: str,
) -> list[Paragraph]:
    """Колонка одного языка: вводная фраза и пронумерованные обязательства."""
    intro_style = ParagraphStyle(
        name=f"intro-{language}",
        fontName=SANS,
        fontSize=layout.intro_size,
        leading=layout.intro_size + 2,
        spaceAfter=9,
    )
    statement_style = ParagraphStyle(
        name=f"statement-{language}",
        fontName=SANS,
        fontSize=layout.statement_size,
        leading=layout.statement_leading,
        spaceAfter=5,
        leftIndent=11,
        firstLineIndent=-11,
    )
    return [
        Paragraph(getattr(form.intro, language), intro_style),
        *(
            Paragraph(f"{index}. {getattr(statement, language)}", statement_style)
            for index, statement in enumerate(form.statements, start=1)
        ),
    ]


def _draw_column(
    canvas: Canvas,
    paragraphs: list[Paragraph],
    x: float,
    y_top: float,
    width: float,
) -> float:
    """Выложить абзацы сверху вниз. Возвращает нижнюю границу колонки."""
    y = y_top
    for paragraph in paragraphs:
        _, height = paragraph.wrap(width, y_top)
        y -= height
        paragraph.drawOn(canvas, x, y)
        y -= paragraph.style.spaceAfter
    return y


def draw_waiver(canvas: Canvas, form: WaiverForm, layout: WaiverLayout) -> None:
    """Нарисовать бланк расписки на текущей странице."""
    center = layout.page_width / 2
    y = layout.page_height - layout.margin - layout.title_size

    for line in form.title.lines():
        size = fit_size(line, SANS_BOLD, layout.content_width, layout.title_size, min_size=8)
        centred_string(canvas, center, y, line, SANS_BOLD, size)
        y -= layout.title_size + 3

    y -= 8
    meta = (
        RACE.title.ru,
        RACE.title.kk,
        f"{RACE.date.ru} · {RACE.place.ru} · {RACE.distance.ru}",
        f"{RACE.date.kk} · {RACE.place.kk} · {RACE.distance.kk}",
    )
    for line in meta:
        size = fit_size(line, SANS, layout.content_width, layout.meta_size, min_size=6)
        centred_string(canvas, center, y, line, SANS, size, GREY)
        y -= layout.meta_size + 2.5

    y -= 8 * mm

    for block in form.blocks:
        if block.heading is not None:
            canvas.saveState()
            canvas.setFont(SANS_BOLD, layout.label_size + 0.5)
            canvas.drawString(layout.margin, y, block.heading.one_line())
            canvas.restoreState()
            y -= 7 * mm
        for row in block.rows:
            _draw_field_row(canvas, layout, y, row)
            y -= layout.field_step
        y -= 2 * mm

    columns = (
        (layout.margin, "ru"),
        (layout.margin + layout.column_width + layout.column_gutter, "kk"),
    )
    bottom = min(
        _draw_column(canvas, _column_flowables(form, layout, language), x, y, layout.column_width)
        for x, language in columns
    )

    footer_height = 22 * mm
    if bottom < layout.margin + footer_height:
        raise ValueError(
            f"бланк «{form.slug}» не помещается на лист: не хватает "
            f"{(layout.margin + footer_height - bottom) / mm:.0f} мм"
        )

    signature_y = max(bottom - 12 * mm, layout.margin + footer_height)
    _draw_field_row(
        canvas,
        layout,
        signature_y,
        (
            Field(Bilingual("Дата", "Күні")),
            Field(Bilingual("Подпись", "Қолы"), weight=1.6),
        ),
    )
    for index, line in enumerate(form.footer_note.lines()):
        centred_string(
            canvas,
            center,
            signature_y - 9 * mm - index * 11,
            line,
            SANS,
            layout.meta_size,
            GREY,
        )


def build_waiver(output: Path, form: WaiverForm, layout: WaiverLayout | None = None) -> Path:
    """Собрать PDF с одним бланком расписки."""
    register_fonts()
    layout = layout or WaiverLayout()

    output.parent.mkdir(parents=True, exist_ok=True)
    canvas = Canvas(str(output), pagesize=(layout.page_width, layout.page_height))
    canvas.setTitle(f"{form.title.ru} · {RACE.short_title}")
    canvas.setAuthor(RACE.organizer)
    canvas.setSubject(RACE.title.ru)
    draw_waiver(canvas, form, layout)
    canvas.showPage()
    canvas.save()
    return output
