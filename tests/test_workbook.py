"""Проверки книги расчёта призовых.

Формулы в книге считает не Python, поэтому кроме структуры мы прогоняем её
через LibreOffice и сверяем с эталонным расчётом из `prizes`.
"""

from __future__ import annotations

import csv
import random
import shutil
import subprocess
from collections.abc import Callable
from pathlib import Path

import pytest
from openpyxl import load_workbook

from ubt_race_docs.prizes import (
    Result,
    distribute,
    even_threshold,
    fund_from_entries,
    total_at,
)
from ubt_race_docs.race import RACE
from ubt_race_docs.workbook import (
    ENTRIES_CELL,
    ENTRY_FEE_CELL,
    FIRST_DATA_ROW,
    FUND_CELL,
    GRID_HALF_WIDTH,
    GRID_POINTS,
    HEADER_ROW,
    OUT_OF_ORDER_WARNING,
    PAID_CELL,
    REMAINDER_CELL,
    ROUNDING_CELL,
    SECOND_PRICE_CELL,
    THRESHOLD_CELL,
    WARNING_CELL,
    build_workbook,
)

PROTOCOL: tuple[tuple[str, float], ...] = (
    ("Гонщик 1", 2052),
    ("Гонщик 2", 2114),
    ("Гонщик 3", 2145),
    ("Гонщик 4", 2160),
    ("Гонщик 5", 2160),
    ("Гонщик 6", 2400),
    ("Гонщик 7", 2401),
)
ENTRIES = 60

REAL_PROTOCOL: tuple[tuple[str, str, float], ...] = (
    ("Kazantsev Ilya", "00:29:26.1", 1766.1),
    ("Троицкий Сергей", "00:29:46.9", 1786.9),
    ("Бижан Ғибадат", "00:29:53.4", 1793.4),
    ("Chernykh Denis", "00:30:21.9", 1821.9),
)


@pytest.fixture(scope="module")
def workbook_path(tmp_path_factory: pytest.TempPathFactory) -> Path:
    return build_workbook(tmp_path_factory.mktemp("workbook") / "prizes.xlsx")


def test_one_sheet_per_category_plus_instructions(workbook_path: Path) -> None:
    book = load_workbook(workbook_path)
    assert book.sheetnames == ["Мужчины", "Женщины", "Инструкция"]


def test_parameters_come_from_the_regulations(workbook_path: Path) -> None:
    sheet = load_workbook(workbook_path)["Мужчины"]
    assert sheet[ENTRY_FEE_CELL].value == RACE.prizes.entry_fee
    assert sheet[SECOND_PRICE_CELL].value == RACE.prizes.tenge_per_second
    assert sheet[ROUNDING_CELL].value == RACE.prizes.payout_step
    assert sheet[FUND_CELL].value == "=$D$4*$D$5"


def test_entry_count_comes_from_the_names_not_the_times(workbook_path: Path) -> None:
    # Взнос платит и тот, кто потом сошёл: у него есть фамилия, но нет результата.
    sheet = load_workbook(workbook_path)["Мужчины"]
    assert sheet[ENTRIES_CELL].value.startswith("=COUNTA($C$")


def test_protocol_columns_are_marked_as_input(workbook_path: Path) -> None:
    sheet = load_workbook(workbook_path)["Мужчины"]
    headers = {sheet.cell(HEADER_ROW, index).value for index in range(1, 9)}
    assert {"Место", "Номер", "Участник", "Результат", "К выдаче, ₸"} <= headers
    for letter in ("B", "C", "D"):
        assert sheet[f"{letter}{FIRST_DATA_ROW}"].fill.fgColor.rgb.endswith("FFF2CC")


def test_time_is_parsed_by_hand_not_by_value(workbook_path: Path) -> None:
    # Apple Numbers не умеет ни VALUE("0:34:12"), ни VALUE("26.1"),
    # поэтому время разбирается по двоеточиям и точке.
    sheet = load_workbook(workbook_path)["Мужчины"]
    formula = sheet[f"E{FIRST_DATA_ROW}"].value
    assert "LEFT(" in formula and "MID(" in formula
    assert f"VALUE($D{FIRST_DATA_ROW})*86400" not in formula


def test_threshold_is_searched_over_a_grid(workbook_path: Path) -> None:
    sheet = load_workbook(workbook_path)["Мужчины"]
    assert "MAX(" in sheet[THRESHOLD_CELL].value
    assert "SUMPRODUCT" in sheet[f"S{FIRST_DATA_ROW}"].value


def test_row_count_is_validated(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="хотя бы одна строка"):
        build_workbook(tmp_path / "prizes.xlsx", rows=0)


def threshold_like_the_sheet(results: list[Result], fund: int) -> float | None:
    """Повторить перебор, который делает книга: сетка вокруг ровного порога."""
    start = round(even_threshold(results, fund, RACE.prizes), 1) - GRID_HALF_WIDTH
    step = 2 * GRID_HALF_WIDTH / GRID_POINTS
    fitting = [
        round(start + index * step, 6)
        for index in range(GRID_POINTS)
        if total_at(round(start + index * step, 6), results, RACE.prizes) <= fund
    ]
    return max(fitting) if fitting else None


@pytest.mark.parametrize("seed", range(30))
def test_grid_of_the_sheet_finds_the_same_threshold(seed: int) -> None:
    # Книга перебирает 200 порогов вокруг ровного — проверяем, что этого
    # хватает и она приходит к тому же ответу, что и эталонный расчёт.
    random.seed(seed)
    riders = random.randint(1, 60)
    spread = random.choice([3, 30, 300, 900])
    base = random.uniform(1600, 2000)
    seconds = sorted(round(base + random.uniform(0, spread), 1) for _ in range(riders))
    results = [Result(name=str(index), seconds=value) for index, value in enumerate(seconds)]
    fund = fund_from_entries(random.randint(riders, riders + 40))

    assert threshold_like_the_sheet(results, fund) == pytest.approx(
        distribute(results, fund).threshold
    )


def cell(table: list[list[str]], address: str) -> str:
    """Значение ячейки по её адресу вида «I4» в выгруженной таблице."""
    column = ord(address[0]) - ord("A")
    return table[int(address[1:]) - 1][column]


def number(text: str) -> float:
    """Число из ячейки: LibreOffice печатает разряды через пробел."""
    return float(text.replace("\xa0", "").replace(" ", "").replace(",", ".") or 0)


def recalculate(path: Path, tmp_path: Path) -> list[list[str]]:
    """Пересчитать книгу LibreOffice и вернуть лист «Мужчины» как таблицу."""
    profile = tmp_path / "profile"
    outdir = tmp_path / "csv"
    subprocess.run(
        [
            "soffice",
            f"-env:UserInstallation=file://{profile}",
            "--headless",
            "--convert-to",
            "csv:Text - txt - csv (StarCalc):44,34,76,1,,0,false,true,true,false,false,-1",
            "--outdir",
            str(outdir),
            str(path),
        ],
        check=True,
        capture_output=True,
        timeout=300,
    )
    exported = outdir / f"{path.stem}-Мужчины.csv"
    with exported.open(encoding="utf-8", newline="") as handle:
        return list(csv.reader(handle))


def fill(
    path: Path, rows: list[tuple[str, str | float | None]], entries: int | None = None
) -> None:
    """Вставить протокол так, как это сделает судья."""
    book = load_workbook(path)
    sheet = book["Мужчины"]
    for index, (name, shown) in enumerate(rows):
        row = FIRST_DATA_ROW + index
        sheet[f"B{row}"] = 100 + index
        sheet[f"C{row}"] = name
        if shown is not None:
            sheet[f"D{row}"] = shown
    if entries is not None:
        sheet[ENTRIES_CELL] = entries
    book.save(path)


TIME_FORMATS: dict[str, Callable[[float], str | float]] = {
    # Как судья может вставить одно и то же время.
    "чч:мм:сс": lambda s: f"{int(s) // 3600}:{int(s) % 3600 // 60:02d}:{int(s) % 60:02d}",
    "мм:сс": lambda s: f"{int(s) // 60}:{int(s) % 60:02d}",
    "секунды": lambda s: s,
    "доля суток": lambda s: s / 86400,
    # Так «34:12» выглядит после того, как Excel прочитал его как 34 ч 12 мин.
    "мм:сс числом": lambda s: s / 1440,
}


@pytest.mark.skipif(shutil.which("soffice") is None, reason="LibreOffice не установлен")
@pytest.mark.parametrize("time_format", list(TIME_FORMATS), ids=list(TIME_FORMATS))
def test_formulas_match_the_reference_calculation(
    workbook_path: Path, tmp_path: Path, time_format: str
) -> None:
    path = tmp_path / "filled.xlsx"
    shutil.copy(workbook_path, path)
    render = TIME_FORMATS[time_format]
    fill(path, [(name, render(seconds)) for name, seconds in PROTOCOL], entries=ENTRIES)
    table = recalculate(path, tmp_path)

    expected = distribute(
        [Result(name=name, seconds=seconds) for name, seconds in PROTOCOL],
        fund_from_entries(ENTRIES),
    )
    rows = table[HEADER_ROW : HEADER_ROW + len(PROTOCOL)]

    assert [number(row[4]) for row in rows] == [seconds for _, seconds in PROTOCOL]
    assert [number(row[7]) for row in rows] == [payout.amount for payout in expected.payouts]
    assert number(cell(table, THRESHOLD_CELL)) == pytest.approx(expected.threshold, abs=0.05)
    assert number(cell(table, PAID_CELL)) == expected.total_paid
    assert number(cell(table, REMAINDER_CELL)) == expected.remainder
    assert cell(table, WARNING_CELL) == ""


@pytest.mark.skipif(shutil.which("soffice") is None, reason="LibreOffice не установлен")
def test_real_protocol_spends_the_whole_fund(workbook_path: Path, tmp_path: Path) -> None:
    # Протокол мужской группы: время с десятыми, фонд из четырёх взносов.
    path = tmp_path / "real.xlsx"
    shutil.copy(workbook_path, path)
    fill(path, [(name, shown) for name, shown, _ in REAL_PROTOCOL])
    table = recalculate(path, tmp_path)

    rows = table[HEADER_ROW : HEADER_ROW + len(REAL_PROTOCOL)]
    assert [number(row[4]) for row in rows] == [seconds for _, _, seconds in REAL_PROTOCOL]
    assert [number(row[7]) for row in rows] == [3000, 1000, 0, 0]
    assert number(cell(table, PAID_CELL)) == 4000
    assert number(cell(table, REMAINDER_CELL)) == 0


@pytest.mark.skipif(shutil.which("soffice") is None, reason="LibreOffice не установлен")
def test_rider_without_a_result_pays_but_does_not_race(workbook_path: Path, tmp_path: Path) -> None:
    path = tmp_path / "dnf.xlsx"
    shutil.copy(workbook_path, path)
    fill(path, [*[(name, seconds) for name, seconds in PROTOCOL], ("Сошедший", None)])
    table = recalculate(path, tmp_path)

    assert number(cell(table, ENTRIES_CELL)) == len(PROTOCOL) + 1, "сошедший тоже платил взнос"
    dnf = table[HEADER_ROW + len(PROTOCOL)]
    assert dnf[0] == "", "сошедшему место не полагается"
    assert dnf[4] == "", "и результата у него нет"


@pytest.mark.skipif(shutil.which("soffice") is None, reason="LibreOffice не установлен")
def test_protocol_in_the_wrong_order_is_flagged(workbook_path: Path, tmp_path: Path) -> None:
    path = tmp_path / "shuffled.xlsx"
    shutil.copy(workbook_path, path)
    reversed_protocol = sorted(PROTOCOL, key=lambda row: row[1], reverse=True)
    fill(path, list(reversed_protocol), entries=ENTRIES)
    table = recalculate(path, tmp_path)
    assert cell(table, WARNING_CELL) == OUT_OF_ORDER_WARNING
