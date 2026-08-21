"""Проверки модели кубка и параметров, которые уходят в openscad."""

import re
import shutil
from pathlib import Path

import pytest

from ubt_race_docs import trophies
from ubt_race_docs.fonts import SANS_BOLD, text_width
from ubt_race_docs.race import CATEGORIES
from ubt_race_docs.trophies import (
    MODEL_PATH,
    RenderTask,
    openscad_command,
    openscad_executable,
    render,
    render_plan,
    scad_string,
)

ASCENT = 0.7598
"""Доля em, по которой OpenSCAD отмеряет `size` у текста в DejaVu."""

METRICS_SLOP = 1.06
"""Запас: метрики openscad и reportlab совпадают не до последней десятой."""


def model_number(name: str) -> float:
    """Числовой параметр модели — читаем прямо из .scad, чтобы не разъехалось."""
    match = re.search(rf"^{name} = ([0-9.]+);", MODEL_PATH.read_text(encoding="utf-8"), re.M)
    assert match is not None, f"в модели нет параметра {name}"
    return float(match.group(1))


def test_model_is_shipped_with_the_package() -> None:
    assert MODEL_PATH.is_file()
    assert MODEL_PATH.read_text(encoding="utf-8").strip()


def test_model_declares_every_parameter_we_pass() -> None:
    model = MODEL_PATH.read_text(encoding="utf-8")
    for task in render_plan():
        for name in ("part", *task.definitions):
            assert f"{name} =" in model, f"в модели нет параметра {name}"


def test_one_trophy_per_category_for_the_winner() -> None:
    assert [trophy.category for trophy in trophies.trophies()] == list(CATEGORIES)
    assert {trophy.place for trophy in trophies.trophies()} == {1}


def test_plan_cuts_the_shared_cup_once() -> None:
    plan = render_plan()
    filenames = [task.filename for task in plan]
    assert len(filenames) == len(set(filenames))
    assert filenames.count("trophy-cup.stl") == 1
    assert "trophy-base-men.stl" in filenames
    assert "trophy-base-women.stl" in filenames


def test_engraving_carries_the_race_place_and_category() -> None:
    base = next(task for task in render_plan() if task.filename == "trophy-base-women.stl")
    assert base.definitions["category_line"] == "Женщины · Әйелдер"
    assert base.definitions["place_line"] == "1 место · 1-орын"
    assert base.definitions["title_line"] == "UBT TT · 04.10.2026"


def test_command_passes_definitions_and_model(tmp_path: Path) -> None:
    task = RenderTask("trophy.stl", "base", {"place_line": "1 место"}, "тест")
    command = openscad_command(tmp_path / "trophy.stl", task, executable="/usr/bin/openscad")
    assert command[0] == "/usr/bin/openscad"
    assert command[1:3] == ["-o", str(tmp_path / "trophy.stl")]
    assert "-D" in command
    assert 'part="base"' in command
    assert 'place_line="1 место"' in command
    assert command[-1] == str(MODEL_PATH)


def test_missing_openscad_is_reported_clearly(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(shutil, "which", lambda _: None)
    with pytest.raises(RuntimeError, match="не найден openscad"):
        render(tmp_path / "trophy.stl", render_plan()[0])


@pytest.mark.skipif(openscad_executable() is None, reason="openscad не установлен")
def test_model_compiles_with_the_engraving(tmp_path: Path) -> None:
    # Экспорт в CSG не считает геометрию, поэтому быстрый: проверяем,
    # что модель разбирается и наши -D реально доезжают до надписей.
    task = next(task for task in render_plan() if task.filename == "trophy-base-men.stl")
    output = render(tmp_path / "trophy.csg", task)
    csg = output.read_text(encoding="utf-8")
    assert "Мужчины · Ерлер" in csg
    assert "1 место · 1-орын" in csg


def test_model_engraves_with_the_font_we_ship() -> None:
    assert 'font_name = "DejaVu Sans' in MODEL_PATH.read_text(encoding="utf-8")


def test_engraving_fits_the_flat_face_of_the_plinth() -> None:
    # Гравировка режется по передней грани подставки; за скруглением углов
    # буквы теряют глубину, поэтому строка должна укладываться в плоскую часть.
    flat_half_width = model_number("base_width") / 2 - model_number("base_corner")
    em = model_number("text_size") / ASCENT
    for task in render_plan():
        for name, line in task.definitions.items():
            half = text_width(line, SANS_BOLD, em) / 2 * METRICS_SLOP
            assert half <= flat_half_width, (
                f"{name} = {line!r} шире плоской части подставки: "
                f"{half:.1f} мм против {flat_half_width:.1f} мм"
            )


def test_captions_with_quotes_stay_valid_openscad() -> None:
    assert scad_string("1 место") == '"1 место"'
    assert scad_string('кубок "UBT"') == '"кубок \\"UBT\\""'
    assert scad_string("путь\\сюда") == '"путь\\\\сюда"'


def test_command_escapes_the_caption(tmp_path: Path) -> None:
    task = RenderTask("trophy.stl", "base", {"place_line": '1 "место"'}, "тест")
    command = openscad_command(tmp_path / "trophy.stl", task)
    assert 'place_line="1 \\"место\\""' in command
