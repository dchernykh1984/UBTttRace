"""Эксель для расчёта призовых.

Судья вставляет протокол категории (номер, участник, результат) в жёлтую зону,
всё остальное считают формулы прямо в книге — пересчёт мгновенный, ничего
запускать не нужно. Правила распределения те же, что в `prizes`.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.worksheet.worksheet import Worksheet

from .race import CATEGORIES, RACE

DEFAULT_ROWS = 200
HEADER_ROW = 10
FIRST_DATA_ROW = HEADER_ROW + 1

# Как разбирается вставленный результат (колонка L → колонка «Время, с»):
#   меньше 0.5 — Excel уже понял ячейку как время, это доля суток → ×86400;
#   меньше 100 — так выглядит «34:12»: Excel читает такую запись как 34 часа
#                12 минут, ровно в 60 раз больше правды (1.425 суток вместо
#                2052 секунд) → ×1440;
#   иначе      — это просто секунды.
# Настоящий результат на 25 км в диапазон 0.5…100 попасть не может, поэтому
# развилка однозначная.
MONEY_FORMAT = "# ##0"
SECONDS_FORMAT = "# ##0"

HEADER_FILL = PatternFill("solid", fgColor="1F3864")
INPUT_FILL = PatternFill("solid", fgColor="FFF2CC")
PARAMETER_FILL = PatternFill("solid", fgColor="E2EFDA")
HEADER_FONT = Font(bold=True, color="FFFFFF", size=10)
TITLE_FONT = Font(bold=True, size=14)
HINT_FONT = Font(size=9, color="808080")
THIN = Side(style="thin", color="BFBFBF")
CELL_BORDER = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)


@dataclass(frozen=True, slots=True)
class Column:
    """Колонка таблицы результатов."""

    letter: str
    header: str
    width: float
    number_format: str | None = None
    formula: str | None = None
    """Шаблон формулы; `{row}` подставляется номером строки, `{last}` — последней."""

    editable: bool = False


COLUMNS: tuple[Column, ...] = (
    Column("A", "Место", 7, SECONDS_FORMAT, '=IF($D{row}="","",ROW()-{header})'),
    Column("B", "Номер", 8, editable=True),
    Column("C", "Участник", 30, editable=True),
    Column("D", "Результат", 13, editable=True),
    Column(
        "E",
        "Время, с",
        10,
        SECONDS_FORMAT,
        '=IF($L{row}="","",ROUND(IF($L{row}<0.5,$L{row}*86400,'
        "IF($L{row}<100,$L{row}*1440,$L{row})),0))",
    ),
    Column(
        "F",
        "Отрыв до следующего, с",
        12,
        SECONDS_FORMAT,
        '=IF(OR($E{row}="",$E{next}=""),"",$E{next}-$E{row})',
    ),
    Column("G", "Стоимость шага, ₸", 13, MONEY_FORMAT, '=IF($F{row}="","",$A{row}*$F{row}*$B$7)'),
    Column(
        "H", "Нарастающим итогом, ₸", 15, MONEY_FORMAT, '=IF($G{row}="","",SUM($G${first}:$G{row}))'
    ),
    Column("I", "Шаг оплачен", 9, None, '=IF($H{row}="","",IF($H{row}<=$B$6,1,0))'),
    Column(
        "J",
        "Приз до округления, ₸",
        15,
        MONEY_FORMAT,
        '=IF($D{row}="","",SUMIFS($F${first}:$F${last},$A${first}:$A${last},'
        '">="&$A{row},$I${first}:$I${last},1)*$B$7)',
    ),
    Column("K", "К выдаче, ₸", 12, MONEY_FORMAT, '=IF($J{row}="","",FLOOR($J{row},$B$8))'),
    Column(
        "L",
        "служебное: разбор времени",
        22,
        None,
        '=IF($D{row}="","",IF(ISNUMBER($D{row}),$D{row},IFERROR(VALUE($D{row}),"")))',
    ),
)

PARAMETERS: tuple[tuple[str, str, str], ...] = (
    ("A4", "Стартовый взнос, ₸", "B4"),
    ("A5", "Оплатило взносов, чел.", "B5"),
    ("A6", "Призовой фонд, ₸", "B6"),
    ("A7", "Цена секунды, ₸", "B7"),
    ("A8", "Округление выплаты, ₸", "B8"),
)

INSTRUCTIONS: tuple[tuple[str, bool], ...] = (
    ("Как считать призовые", True),
    ("", False),
    ("1. Откройте лист нужной категории — «Мужчины» или «Женщины». Фонды раздельные:", False),
    ("   взносы женщин разыгрываются среди женщин, взносы мужчин — среди мужчин.", False),
    ("2. Вставьте протокол в жёлтые колонки «Номер», «Участник», «Результат»,", False),
    ("   начиная со строки 11, в порядке финиша — от лучшего времени к худшему.", False),
    ("   Сошедших и дисквалифицированных не вставляйте.", False),
    ("3. Результат понимается в любом виде: 0:34:12, 34:12 или числом секунд 2052.", False),
    ("4. Проверьте «Оплатило взносов»: там формула, считающая заполненные строки.", False),
    ("   Если кто-то заплатил взнос, но не финишировал, впишите число руками.", False),
    ("5. Колонка «К выдаче» — это то, что вручается наличными.", False),
    ("", False),
    ("Правило из положения", True),
    ("", False),
    ("Каждая выигранная по протоколу секунда стоит 100 ₸: сначала победитель получает", False),
    ("за отрыв от второго, затем первые двое — за отрыв от третьего, и так далее,", False),
    ("пока призовой фонд не кончится. Кому не хватило — тот без приза.", False),
    ("", False),
    ("Шаг, на который остатка фонда не хватает целиком, не оплачивается вовсе,", False),
    ("и распределение на нём останавливается. Итог каждого округляется вниз", False),
    ("до 1000 ₸ — чтобы выдавать тысячными купюрами и не выйти за фонд.", False),
    ("", False),
    ("Колонки после «Время, с» — расчётные, их менять не нужно.", False),
    ("Колонка L служебная: она разбирает то, что вставили в «Результат».", False),
)


def _write_header(sheet: Worksheet, title: str, last_row: int) -> None:
    sheet["A1"] = title
    sheet["A1"].font = TITLE_FONT
    sheet["A2"] = (
        "Вставьте протокол в жёлтые колонки начиная со строки 11 — остальное посчитается само."
    )
    sheet["A2"].font = HINT_FONT

    values = {
        "B4": RACE.prizes.entry_fee,
        "B5": f"=COUNT($E${FIRST_DATA_ROW}:$E${last_row})",
        "B6": "=$B$4*$B$5",
        "B7": RACE.prizes.tenge_per_second,
        "B8": RACE.prizes.payout_step,
    }
    for label_cell, label, value_cell in PARAMETERS:
        sheet[label_cell] = label
        sheet[label_cell].font = Font(bold=True, size=10)
        sheet[value_cell] = values[value_cell]
        sheet[value_cell].number_format = MONEY_FORMAT
        sheet[value_cell].fill = PARAMETER_FILL
        sheet[value_cell].border = CELL_BORDER

    totals = (
        ("D4", "Выплачено, ₸", "E4", f"=SUM($K${FIRST_DATA_ROW}:$K${last_row})"),
        ("D5", "Остаток фонда, ₸", "E5", "=$B$6-$E$4"),
        ("D6", "Призёров", "E6", f'=COUNTIF($K${FIRST_DATA_ROW}:$K${last_row},">0")'),
    )
    for label_cell, label, value_cell, formula in totals:
        sheet[label_cell] = label
        sheet[label_cell].font = Font(bold=True, size=10)
        sheet[value_cell] = formula
        sheet[value_cell].number_format = MONEY_FORMAT
        sheet[value_cell].border = CELL_BORDER


def _write_table(sheet: Worksheet, last_row: int) -> None:
    for column in COLUMNS:
        cell = sheet[f"{column.letter}{HEADER_ROW}"]
        cell.value = column.header
        cell.font = HEADER_FONT
        cell.fill = HEADER_FILL
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        sheet.column_dimensions[column.letter].width = column.width

    sheet.row_dimensions[HEADER_ROW].height = 32

    for row in range(FIRST_DATA_ROW, last_row + 1):
        for column in COLUMNS:
            cell = sheet[f"{column.letter}{row}"]
            if column.formula is not None:
                cell.value = column.formula.format(
                    row=row,
                    next=row + 1,
                    first=FIRST_DATA_ROW,
                    last=last_row,
                    header=HEADER_ROW,
                )
            if column.number_format is not None:
                cell.number_format = column.number_format
            if column.editable:
                cell.fill = INPUT_FILL
            cell.border = CELL_BORDER

    sheet[f"K{HEADER_ROW}"].font = Font(bold=True, color="FFFFFF", size=10)
    sheet.freeze_panes = f"A{FIRST_DATA_ROW}"


def _write_instructions(sheet: Worksheet) -> None:
    sheet.column_dimensions["A"].width = 100
    for index, (line, is_heading) in enumerate(INSTRUCTIONS, start=1):
        cell = sheet[f"A{index}"]
        cell.value = line
        cell.font = Font(bold=True, size=12) if is_heading else Font(size=11)


def build_workbook(output: Path, rows: int = DEFAULT_ROWS) -> Path:
    """Собрать книгу с листом на каждую категорию и инструкцией."""
    if rows < 1:
        raise ValueError(f"в таблице должна быть хотя бы одна строка, получено {rows}")

    last_row = HEADER_ROW + rows
    book = Workbook()
    book.remove(book.active)

    for category in CATEGORIES:
        sheet = book.create_sheet(category.name.ru)
        _write_header(sheet, f"{category.name.one_line()} — призовые", last_row)
        _write_table(sheet, last_row)

    _write_instructions(book.create_sheet("Инструкция"))

    book.properties.title = f"Призовые · {RACE.short_title}"
    book.properties.creator = RACE.organizer
    book.properties.subject = RACE.title.ru

    output.parent.mkdir(parents=True, exist_ok=True)
    book.save(output)
    return output
