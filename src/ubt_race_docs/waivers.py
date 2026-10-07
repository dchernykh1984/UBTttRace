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
    margin: float = 12 * mm
    column_gutter: float = 6 * mm
    title_size: float = 13
    meta_size: float = 8
    intro_size: float = 8.5
    label_size: float = 8
    statement_size: float = 7.2
    statement_leading: float = 8.8
    field_step: float = 10 * mm
    # Подпись с датой и строчкой «сдаётся при регистрации». Место под неё
    # резервируется заранее: подпись не должна оставаться одна на обороте.
    footer_height: float = 18 * mm

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
            "Мне исполнилось 18 лет. Я ознакомлен(а) с положением мероприятия, согласен(на) "
            "с ним и обязуюсь соблюдать его и указания судей и волонтёров.",
            "Маған 18 жас толды. Мен іс-шара ережесімен таныстым, онымен келісемін және оны, "
            "сондай-ақ төрешілер мен еріктілердің нұсқауларын сақтауға міндеттенемін.",
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
            "Состояние моего здоровья позволяет мне участвовать, медицинских противопоказаний "
            "у меня нет; оценку своего состояния я делаю сам(а). Я не нахожусь под действием "
            "алкоголя, наркотических или психотропных веществ.",
            "Денсаулығымның жағдайы қатысуға мүмкіндік береді, медициналық қарсы көрсетілімдерім "
            "жоқ; өз жағдайымды өзім бағалаймын. Мен алкогольдің, есірткі немесе психотроптық "
            "заттардың әсерінде емеспін.",
        ),
        Bilingual(
            "Я понимаю, что езда на велосипеде связана с риском падения, травмы, увечья и гибели, "
            "и принимаю этот риск на себя. Организаторы не перекрывают дорогу, не обеспечивают "
            "медицинское сопровождение и не страхуют участников — страхование моя забота.",
            "Велосипед тебу құлау, жарақат алу, мүгедек болу және қаза болу қаупімен байланысты "
            "екенін түсінемін және бұл тәуекелді өз мойныма аламын. Ұйымдастырушылар жолды "
            "жаппайды, медициналық алып жүруді қамтамасыз етпейді және қатысушыларды "
            "сақтандырмайды — сақтандыру менің міндетім.",
        ),
        Bilingual(
            "Я стартую на исправном велосипеде и в застёгнутом шлеме.",
            "Мен ақаусыз велосипедпен және тағылған шлеммен старт аламын.",
        ),
        Bilingual(
            "Вред, причинённый мной другим участникам, иным лицам или их имуществу, возмещаю я.",
            "Басқа қатысушыларға, өзге адамдарға немесе олардың мүлкіне келтірген зиянымды "
            "мен өтеймін.",
        ),
        Bilingual(
            "Ответственность за свою жизнь, здоровье и имущество я несу самостоятельно и не буду "
            "предъявлять организаторам претензий — кроме случаев, когда вред причинён по их вине.",
            "Өз өмірім, денсаулығым және мүлкім үшін жауапкершілікті өзім көтеремін және "
            "ұйымдастырушыларға наразылық білдірмеймін — зиян олардың кінәсінен келтірілген "
            "жағдайларды қоспағанда.",
        ),
        Bilingual(
            "Я согласен(на) на оказание мне первой помощи и на вызов скорой помощи. Организатор "
            "вправе не допустить меня к старту или снять с дистанции при нарушении правил, "
            "опасной езде или явной угрозе моему здоровью.",
            "Маған алғашқы көмек көрсетуге және жедел жәрдем шақыруға келісемін. Ұйымдастырушы "
            "ережені бұзған, қауіпті жүрген немесе денсаулығыма анық қауіп төнген жағдайда мені "
            "старттан шеттетуге немесе қашықтықтан алып тастауға құқылы.",
        ),
        Bilingual(
            f"Я даю согласие {RACE.organizer} на сбор и обработку указанных здесь персональных "
            "данных — фамилии, имени, отчества, даты рождения, телефона и контакта для экстренной "
            "связи, который я указал(а) с согласия этого человека, — чтобы допустить меня "
            "к старту, обеспечить безопасность и составить "
            "и опубликовать стартовые протоколы и результаты, в том числе на сайте организатора "
            "и в его аккаунтах в социальных сетях. Согласие действует до отзыва; отозвать его "
            "можно письменным обращением к организатору.",
            f"Мен {RACE.organizer} ұйымына осында көрсетілген дербес деректерімді — тегім, атым, "
            "әкемнің аты, туған күнім, телефоным және сол адамның келісімімен көрсетілген төтенше "
            "байланыс контактісі — мені стартқа "
            "жіберу, қауіпсіздікті қамтамасыз ету, старттық хаттамалар мен нәтижелерді жасау және "
            "жариялау, оның ішінде ұйымдастырушының сайтында және әлеуметтік желілердегі "
            "аккаунттарында жариялау үшін жинауға және өңдеуге келісім беремін. Келісім ол кері "
            "қайтарылғанға дейін қолданылады; оны ұйымдастырушыға жазбаша жүгіну арқылы кері "
            "қайтаруға болады.",
        ),
        Bilingual(
            "Я согласен(на) на фото- и видеосъёмку на мероприятии и на использование этих "
            "материалов организатором и его партнёрами без ограничения срока и территории "
            "и без вознаграждения мне, в том числе для рассказа о мероприятии и его рекламы.",
            "Іс-шарада фото- және бейнетүсірілім жүргізілуіне және бұл материалдарды "
            "ұйымдастырушы мен оның серіктестері мерзімі мен аумағы шектелмей, маған сыйақы "
            "төленбей, оның ішінде іс-шара туралы айту және оны жарнамалау үшін пайдалануына "
            "келісемін.",
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
            "Я законный представитель указанного несовершеннолетнего и даю согласие на его "
            "участие. Я ознакомлен(а) с положением мероприятия и обеспечу его соблюдение "
            "ребёнком, включая указания судей и волонтёров.",
            "Мен көрсетілген кәмелетке толмаған баланың заңды өкілімін және оның қатысуына "
            "келісім беремін. Мен іс-шара ережесімен таныстым және оны, сондай-ақ төрешілер мен "
            "еріктілердің нұсқауларын баланың сақтауын қамтамасыз етемін.",
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
            "и принимаю этот риск на себя. Организаторы не перекрывают дорогу, не обеспечивают "
            "медицинское сопровождение и не страхуют участников — страхование моя забота.",
            "Велосипед тебу құлау, жарақат алу, мүгедек болу және қаза болу қаупімен байланысты "
            "екенін түсінемін және бұл тәуекелді өз мойныма аламын. Ұйымдастырушылар жолды "
            "жаппайды, медициналық алып жүруді қамтамасыз етпейді және қатысушыларды "
            "сақтандырмайды — сақтандыру менің міндетім.",
        ),
        Bilingual(
            "Ребёнок стартует на исправном велосипеде и в застёгнутом шлеме.",
            "Бала ақаусыз велосипедпен және тағылған шлеммен старт алады.",
        ),
        Bilingual(
            "Вред, причинённый ребёнком другим участникам, иным лицам или их имуществу, "
            "возмещаю я.",
            "Баланың басқа қатысушыларға, өзге адамдарға немесе олардың мүлкіне келтірген зиянын "
            "мен өтеймін.",
        ),
        Bilingual(
            "Ответственность за жизнь, здоровье и имущество ребёнка несу я и не буду предъявлять "
            "организаторам претензий — кроме случаев, когда вред причинён по их вине.",
            "Баланың өмірі, денсаулығы және мүлкі үшін жауапкершілікті мен көтеремін және "
            "ұйымдастырушыларға наразылық білдірмеймін — зиян олардың кінәсінен келтірілген "
            "жағдайларды қоспағанда.",
        ),
        Bilingual(
            "Я согласен(на) на оказание ребёнку первой помощи и на вызов скорой помощи. "
            "Организатор вправе не допустить ребёнка к старту или снять его с дистанции при "
            "нарушении правил, опасной езде или явной угрозе его здоровью.",
            "Балаға алғашқы көмек көрсетуге және жедел жәрдем шақыруға келісемін. Ұйымдастырушы "
            "ережені бұзған, қауіпті жүрген немесе денсаулығына анық қауіп төнген жағдайда баланы "
            "старттан шеттетуге немесе қашықтықтан алып тастауға құқылы.",
        ),
        Bilingual(
            f"Я даю согласие {RACE.organizer} на сбор и обработку указанных здесь персональных "
            "данных — своих и ребёнка, включая контакт для экстренной связи, указанный мной "
            "с согласия этого человека, — чтобы допустить ребёнка к старту, обеспечить "
            "безопасность и составить и опубликовать стартовые протоколы и результаты, на сайте "
            "организатора и в его аккаунтах в социальных сетях. Согласие действует до отзыва; "
            "отозвать его можно письменным обращением к организатору.",
            f"Мен {RACE.organizer} ұйымына осында көрсетілген — өзімнің және баламның — дербес "
            "деректерді, оның ішінде сол адамның келісімімен көрсетілген төтенше байланыс "
            "контактісін, баланы стартқа жіберу, қауіпсіздікті қамтамасыз ету, старттық хаттамалар "
            "мен нәтижелерді жасау және жариялау, оның ішінде ұйымдастырушының сайтында және "
            "әлеуметтік желілердегі аккаунттарында жариялау үшін жинауға және өңдеуге келісім "
            "беремін. Келісім ол кері қайтарылғанға дейін қолданылады; оны ұйымдастырушыға "
            "жазбаша жүгіну арқылы кері қайтаруға болады.",
        ),
        Bilingual(
            "Я согласен(на) на фото- и видеосъёмку ребёнка на мероприятии и на использование "
            "этих материалов организатором и его партнёрами без ограничения срока и территории "
            "и без вознаграждения, в том числе для рассказа о мероприятии и его рекламы.",
            "Баланы іс-шарада фото- және бейнетүсіруге және бұл материалдарды ұйымдастырушы мен "
            "оның серіктестері мерзімі мен аумағы шектелмей, сыйақысыз, оның ішінде іс-шара "
            "туралы айту және оны жарнамалау үшін пайдалануына келісемін.",
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
        spaceAfter=7,
    )
    statement_style = ParagraphStyle(
        name=f"statement-{language}",
        fontName=SANS,
        fontSize=layout.statement_size,
        leading=layout.statement_leading,
        spaceAfter=3.5,
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


def _paragraph_height(paragraph: Paragraph, width: float) -> float:
    _, height = paragraph.wrap(width, 10_000)
    return height + paragraph.style.spaceAfter


def _fit_count(
    columns: dict[str, list[Paragraph]],
    width: float,
    available: float,
    start: int,
) -> int:
    """Сколько абзацев начиная с `start` поместится в обеих колонках сразу.

    Ломать колонки надо в одном и том же месте: иначе пункт 7 по-русски
    окажется на первой странице, а по-казахски на второй, и подписывать
    такое нельзя.
    """
    used = 0.0
    count = 0
    for index in range(start, len(next(iter(columns.values())))):
        step = max(_paragraph_height(column[index], width) for column in columns.values())
        if used + step > available:
            break
        used += step
        count += 1
    return count


def _draw_signature(canvas: Canvas, layout: WaiverLayout, form: WaiverForm, y: float) -> None:
    _draw_field_row(
        canvas,
        layout,
        y,
        (
            Field(Bilingual("Дата", "Күні")),
            Field(Bilingual("Подпись", "Қолы"), weight=1.6),
        ),
    )
    for index, line in enumerate(form.footer_note.lines()):
        centred_string(
            canvas,
            layout.page_width / 2,
            y - 9 * mm - index * 11,
            line,
            SANS,
            layout.meta_size,
            GREY,
        )


def draw_waiver(canvas: Canvas, form: WaiverForm, layout: WaiverLayout) -> int:
    """Нарисовать бланк расписки. Возвращает число занятых страниц.

    Бланк начинается с шапки и полей, дальше идут обязательства в две
    колонки. Если они не помещаются, бланк продолжается на обороте —
    на регистрации это всё равно один лист, напечатанный с двух сторон.
    """
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

    y -= 5 * mm

    for block in form.blocks:
        if block.heading is not None:
            canvas.saveState()
            canvas.setFont(SANS_BOLD, layout.label_size + 0.5)
            canvas.drawString(layout.margin, y, block.heading.one_line())
            canvas.restoreState()
            y -= 6 * mm
        for row in block.rows:
            _draw_field_row(canvas, layout, y, row)
            y -= layout.field_step
        y -= 1 * mm

    columns = {language: _column_flowables(form, layout, language) for language in ("ru", "kk")}
    offsets = {
        "ru": layout.margin,
        "kk": layout.margin + layout.column_width + layout.column_gutter,
    }
    total = len(columns["ru"])
    footer_height = layout.footer_height

    pages = 1
    drawn = 0
    while drawn < total:
        # На последней странице под подпись нужно оставить место.
        room = y - layout.margin
        # Если всё оставшееся влезает вместе с подписью — кладём разом.
        # Иначе набиваем страницу целиком: подпись уедет на следующую.
        count = _fit_count(columns, layout.column_width, room - footer_height, drawn)
        if count < total - drawn:
            count = _fit_count(columns, layout.column_width, room, drawn)
        if count == 0:
            raise ValueError(
                f"бланк «{form.slug}» не помещается на лист: не влезает даже один пункт"
            )

        bottom = min(
            _draw_column(
                canvas, column[drawn : drawn + count], offsets[language], y, layout.column_width
            )
            for language, column in columns.items()
        )
        drawn += count

        if drawn < total:
            canvas.showPage()
            pages += 1
            y = layout.page_height - layout.margin
            continue

        signature_y = bottom - 6 * mm
        if signature_y < layout.margin + footer_height:
            canvas.showPage()
            pages += 1
            signature_y = layout.page_height - layout.margin - 10 * mm
        _draw_signature(canvas, layout, form, signature_y)

    return pages


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
