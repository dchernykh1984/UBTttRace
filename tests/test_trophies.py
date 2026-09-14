"""Проверки модели кубка и параметров, которые уходят в openscad."""

import math
import re
import shutil
import subprocess
from pathlib import Path

import pytest

from ubt_race_docs.fonts import SANS_BOLD, text_width
from ubt_race_docs.race import CATEGORIES
from ubt_race_docs.trophies import (
    MODEL_PATH,
    RenderTask,
    openscad_command,
    openscad_executable,
    openscad_features,
    render,
    render_plan,
    scad_string,
)

ASCENT = 0.72
"""Доля em, по которой OpenSCAD отмеряет `size` у текста в DejaVu.

Цифра нарочно занижена: по textmetrics самого OpenSCAD отношение лежит
между 0.726 и 0.741 в зависимости от строки, а так оценка ширины всегда
получается с запасом.
"""

METRICS_SLOP = 1.06
"""Запас: метрики openscad и reportlab совпадают не до последней десятой."""


def model_number(name: str) -> float:
    """Числовой параметр модели — читаем прямо из .scad, чтобы не разъехалось."""
    match = re.search(rf"^{name} = (-?[0-9.]+);", MODEL_PATH.read_text(encoding="utf-8"), re.M)
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


WHEEL_LOGO_RADIUS = 0.5344
"""Радиус эмблемы от её центра в долях высоты.

Габарит у эмблемы прямоугольный, а сама она почти круглая, поэтому по углам
габарита места остаётся больше, чем кажется. Цифра снята с контура: при
высоте 46 мм самая дальняя точка лежит в 24.58 мм от центра.
"""

LOGO_SOURCE_WIDTH = 99.95
"""Ширина контура в `ubt-logo.svg`: с ней он импортируется в OpenSCAD."""


def logo_width(height_parameter: str) -> float:
    """Ширина логотипа при заданной параметром высоте."""
    height = model_number(height_parameter)
    return height / model_number("logo_source_height") * LOGO_SOURCE_WIDTH


def test_logo_fits_the_side_of_the_plinth() -> None:
    # Логотип идёт на боковые грани; за скруглением углов гравировка теряет
    # глубину, поэтому меряем плоскую часть грани.
    flat = model_number("base_depth") - 2 * model_number("base_corner")
    width = logo_width("logo_height")
    assert width < flat, f"логотип шире плоской части: {width:.1f} мм против {flat:.1f} мм"
    assert model_number("logo_height") < model_number("base_height")


def test_logo_fits_the_rear_disc() -> None:
    # На колесе логотип виден лучше всего, но должен остаться в пределах диска.
    # Меряем не габарит, а сам контур: эмблема почти круглая и вписана
    # в диск, поэтому важен её радиус от центра, а не угол габарита.
    radius = model_number("wheel_diameter") / 2
    reach = model_number("wheel_logo_height") * WHEEL_LOGO_RADIUS
    margin = radius - reach
    assert margin > 0.8, f"эмблема подходит к ободу на {margin:.2f} мм"
    assert margin < 3.0, f"на колесе осталось {margin:.1f} мм — эмблему можно крупнее"


def test_wheel_engraving_does_not_pierce_the_disc() -> None:
    # Гравировка идёт с обеих сторон колеса — насквозь она бить не должна.
    assert 2 * model_number("logo_depth") < model_number("frame_thickness") / 2


def test_team_name_is_engraved_large_enough_to_print() -> None:
    # В логотипе надпись «Universal Bicycle Team» занимает нижнюю треть высоты,
    # буква — примерно 0.11 от неё. Тоньше 0.4 мм сопло уже не воспроизводит.
    letter_height = model_number("wheel_logo_height") * 0.11
    assert letter_height > 4, f"буквы на колесе всего {letter_height:.1f} мм"


def test_fast_engine_is_used_when_available(tmp_path: Path) -> None:
    task = RenderTask("trophy.stl", "base", {}, "тест")
    command = openscad_command(
        tmp_path / "trophy.stl", task, features=frozenset({"manifold", "binstl"})
    )
    assert "--backend=manifold" in command
    assert "--export-format=binstl" in command


def test_old_openscad_gets_no_unknown_flags(tmp_path: Path) -> None:
    # Сборка 2021 года о таких ключах не знает и просто не запустится.
    command = openscad_command(tmp_path / "trophy.stl", RenderTask("t.stl", "base", {}, ""))
    assert not [flag for flag in command if flag.startswith("--")]


def test_binary_export_only_for_stl(tmp_path: Path) -> None:
    command = openscad_command(
        tmp_path / "trophy.csg", RenderTask("t.csg", "base", {}, ""), features=frozenset({"binstl"})
    )
    assert "--export-format=binstl" not in command


def test_features_are_read_from_the_help_output(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_help(*_args: object, **_kwargs: object) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess([], 0, stdout="--backend=<name>\n--export-format=<f>\n")

    openscad_features.cache_clear()
    monkeypatch.setattr(subprocess, "run", fake_help)
    assert openscad_features("/usr/bin/openscad") == {"manifold", "binstl"}
    openscad_features.cache_clear()


def test_missing_features_are_reported_as_empty(monkeypatch: pytest.MonkeyPatch) -> None:
    def old_help(*_args: object, **_kwargs: object) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess([], 0, stdout="Usage: openscad [options] file.scad\n")

    openscad_features.cache_clear()
    monkeypatch.setattr(subprocess, "run", old_help)
    assert openscad_features("/usr/bin/openscad-2021") == frozenset()
    openscad_features.cache_clear()


GIANT_SOURCE_WIDTH = 99.81
"""Ширина контура в `giant-logo.svg`."""

GIANT_SOURCE_HEIGHT = 19.19


def test_partner_logo_is_traced_next_to_the_model() -> None:
    logo = MODEL_PATH.parent / "giant-logo.svg"
    assert logo.is_file()
    assert "<svg" in logo.read_text(encoding="utf-8")


def test_partner_logo_fits_the_back_of_the_plinth() -> None:
    flat = model_number("base_length") - 2 * model_number("base_corner")
    length = model_number("giant_base_length")
    assert length < flat, f"логотип партнёра шире плоской части: {length} против {flat}"
    height = length / GIANT_SOURCE_WIDTH * GIANT_SOURCE_HEIGHT
    assert height < model_number("base_height")


PARTNER_PROFILE = ((0.0, 0.15, 0.0963), (0.22, 1.0, 0.0490))
"""Полувысота логотипа партнёра в долях его длины по участкам.

Логотип неоднороден: слева знак в полную высоту, дальше надпись «GIANT»
вдвое ниже. Мерить по общему габариту бессмысленно — рама под ним узкая
и наклонная. Цифры сняты с контура.
"""

FRAME_TUBES = (
    ("нижняя труба", "bottom_bracket", "down_tube_top", "down_tube_width", "down_tube_top_width"),
    # Ширины подседельной, верхней и рулевой стоят в `frame()` числами.
    ("подседельная", "bottom_bracket", "seat_top", 11.0, 9.0),
    ("верхняя труба", "seat_top", "head_top", 6.0, 5.0),
    ("рулевая", "head_top", "head_bottom", 6.5, 6.5),
)


def model_vector(name: str) -> tuple[float, float]:
    """Точка `[x, y]` из модели."""
    match = re.search(
        rf"^{name} = \[(-?[0-9.]+), *(-?[0-9.]+)\];",
        MODEL_PATH.read_text(encoding="utf-8"),
        re.M,
    )
    assert match is not None, f"в модели нет параметра {name}"
    return float(match.group(1)), float(match.group(2))


def frame_depth(point: tuple[float, float]) -> float:
    """Насколько глубоко точка сидит в раме: расстояние до ближайшей кромки.

    Считаем по трубам: каждая — это отрезок с шириной, меняющейся по длине.
    Берём лучшую из труб, поэтому на стыках оценка выходит осторожной.
    """
    best = -math.inf
    for _, first, second, w1, w2 in FRAME_TUBES:
        start, end = model_vector(first), model_vector(second)
        width1 = w1 if isinstance(w1, float) else model_number(w1)
        width2 = w2 if isinstance(w2, float) else model_number(w2)
        span = math.dist(start, end)
        axis = ((end[0] - start[0]) / span, (end[1] - start[1]) / span)
        offset = (point[0] - start[0], point[1] - start[1])
        along = min(span, max(0.0, offset[0] * axis[0] + offset[1] * axis[1]))
        foot = (start[0] + along * axis[0], start[1] + along * axis[1])
        half = (width1 + (width2 - width1) * along / span) / 2
        best = max(best, half - math.dist(point, foot))
    # каретка — круг радиусом 8 вокруг своей точки
    return max(best, 8 - math.dist(point, model_vector("bottom_bracket")))


def test_partner_logo_stays_on_the_frame() -> None:
    # Логотип лежит вдоль нижней трубы по её середине. Заезжать на каретку
    # и подседельную ему можно, а вот вылезать за силуэт рамы — нет.
    start, end = model_vector("bottom_bracket"), model_vector("down_tube_top")
    span = math.dist(start, end)
    axis = ((end[0] - start[0]) / span, (end[1] - start[1]) / span)
    length = model_number("giant_tube_length")
    worst = min(
        frame_depth(
            (
                start[0] + at * axis[0] - side * half * length * axis[1],
                start[1] + at * axis[1] + side * half * length * axis[0],
            )
        )
        for first, last, half in PARTNER_PROFILE
        for edge in (first, last)
        for at in (span / 2 - length / 2 + edge * length,)
        for side in (-1, 1)
    )
    assert worst > 0.8, f"логотип подходит к кромке рамы на {worst:.2f} мм"
    assert worst < 2.5, f"до кромки рамы {worst:.1f} мм — логотип можно крупнее"


def test_engraving_never_cuts_through_the_frame() -> None:
    assert 2 * model_number("logo_depth") < model_number("frame_thickness") / 2


def test_cake_is_cut_as_its_own_part() -> None:
    plan = {task.filename: task for task in render_plan()}
    assert "trophy-cake.stl" in plan
    assert plan["trophy-cake.stl"].part == "cake"
    assert plan["trophy-cake.stl"].definitions == {}, "гравировки на тортике нет"


def test_cake_stands_clear_of_the_bike() -> None:
    # Тортик объёмный: между его боком и плоскостью велосипеда нужен зазор.
    bike_face = model_number("bike_offset_y") - model_number("frame_thickness") / 2
    cake_edge = model_number("cake_offset_y") + model_number("cake_diameter") / 2
    assert cake_edge < bike_face


def test_cake_fits_the_depth_of_the_plinth() -> None:
    bike_edge = abs(model_number("bike_offset_y")) + model_number("frame_thickness") / 2
    assert bike_edge < model_number("base_depth") / 2, "велосипед свисает с подставки"
    cake_edge = abs(model_number("cake_offset_y")) + model_number("cake_diameter") / 2
    assert cake_edge < model_number("base_depth") / 2, "тортик свисает с подставки"


def test_cake_fits_the_length_of_the_plinth() -> None:
    edge = abs(model_number("cake_x")) + model_number("cake_diameter") / 2
    assert edge < model_number("base_length") / 2


def test_cake_narrows_towards_the_top() -> None:
    # Иначе верхний ярус не читается как торт.
    assert model_number("cake_top_diameter") < model_number("cake_diameter")
    assert model_number("candle_diameter") < model_number("cake_top_diameter")


def test_candle_is_thick_enough_to_survive() -> None:
    # Свечка — самая тонкая часть кубка, и держит её только собственный
    # диаметр: подпереть её нечем.
    diameter = model_number("candle_diameter")
    assert diameter >= 4
    assert math.pi * diameter**2 / 4 > 12, "сечение свечки слишком мало"
    assert model_number("candle_height") < 3 * diameter, "слишком длинный рычаг"


def test_cake_sits_in_a_socket_it_can_be_printed_flat_on() -> None:
    # Гнездо, а не шип: с шипом деталь пришлось бы печатать на пятачке.
    source = MODEL_PATH.read_text(encoding="utf-8")
    assert "module cake_socket()" in source
    assert "cake_seat_depth" in source
    assert model_number("cake_seat_depth") < model_number("base_height") / 4
