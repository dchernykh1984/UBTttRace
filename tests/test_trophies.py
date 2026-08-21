"""Проверки модели кубка и параметров, которые уходят в openscad."""

import re
import shutil
from pathlib import Path

import pytest

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


def test_every_category_gets_its_own_base() -> None:
    filenames = [task.filename for task in render_plan()]
    for category in CATEGORIES:
        assert f"trophy-base-{category.code}.stl" in filenames


def test_plan_cuts_the_shared_bike_once() -> None:
    # Велосипед у обоих кубков одинаковый, различаются только подставки.
    filenames = [task.filename for task in render_plan()]
    assert len(filenames) == len(set(filenames))
    assert filenames.count("trophy-bike.stl") == 1


def test_engraving_names_the_winner_not_the_place() -> None:
    plan = {task.filename: task for task in render_plan()}
    women = plan["trophy-base-women.stl"].definitions
    assert women["category_line"] == "Женщины · Әйелдер"
    assert women["place_line"] == "Победительница · Жеңімпаз"
    assert women["title_line"] == "UBT TT · 04.10.2026"
    assert plan["trophy-base-men.stl"].definitions["place_line"] == "Победитель · Жеңімпаз"


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
    assert "Победитель · Жеңімпаз" in csg
    # Логотип на гранях подставки тоже должен доехать до модели.
    assert "ubt-logo.svg" in csg or "polygon" in csg


def test_model_engraves_with_the_font_we_ship() -> None:
    assert 'font_name = "DejaVu Sans' in MODEL_PATH.read_text(encoding="utf-8")


def test_engraving_fits_the_flat_face_of_the_plinth() -> None:
    # Гравировка режется по передней грани подставки; за скруглением углов
    # буквы теряют глубину, поэтому строка должна укладываться в плоскую часть.
    flat_half_width = model_number("base_length") / 2 - model_number("base_corner")
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


def test_logo_is_traced_next_to_the_model() -> None:
    logo = MODEL_PATH.parent / "ubt-logo.svg"
    assert logo.is_file()
    assert "<svg" in logo.read_text(encoding="utf-8")


def test_logo_fits_the_narrowest_engraved_face() -> None:
    # Логотип идёт на три грани, самая узкая — боковая; за скруглением углов
    # гравировка снова теряет глубину, поэтому меряем плоскую часть.
    flat = model_number("base_depth") - 2 * model_number("base_corner")
    source_width, source_height = 99.92, model_number("logo_source_height")
    width = model_number("logo_height") / source_height * source_width
    assert width < flat, f"логотип шире плоской части: {width:.1f} мм против {flat:.1f} мм"
    assert model_number("logo_height") < model_number("base_height")
