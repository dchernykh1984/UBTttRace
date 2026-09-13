"""Проверки медалей участникам."""

import math
import re

from ubt_race_docs.fonts import SANS_BOLD, text_width
from ubt_race_docs.medals import KINDS, MODEL_PATH, render_plan
from ubt_race_docs.race import RACE

ASCENT = 0.7598
"""Доля em, по которой OpenSCAD отмеряет `size` у текста в DejaVu."""


def model_number(name: str) -> float:
    """Числовой параметр модели — читаем прямо из .scad, чтобы не разъехалось."""
    match = re.search(rf"^{name} = (-?[0-9.]+);", MODEL_PATH.read_text(encoding="utf-8"), re.M)
    assert match is not None, f"в модели нет параметра {name}"
    return float(match.group(1))


def test_model_is_shipped_with_the_package() -> None:
    assert MODEL_PATH.is_file()
    assert "part" in MODEL_PATH.read_text(encoding="utf-8")


def test_every_kind_is_cut_into_its_own_file() -> None:
    plan = {task.filename: task for task in render_plan()}
    assert set(plan) == {f"medal-{kind}.stl" for kind, _ in KINDS}
    for task in plan.values():
        assert task.definitions == {}, "надписи медали зашиты в модель"


def test_model_handles_every_kind_we_ask_for() -> None:
    source = MODEL_PATH.read_text(encoding="utf-8")
    for kind, _ in KINDS:
        assert f'part == "{kind}"' in source, f"модель не знает исполнения {kind}"


def test_medal_is_a_fifty_millimetre_disc() -> None:
    assert model_number("medal_diameter") == 50
    assert model_number("medal_thickness") == 5


def test_spacers_match_the_stock_ones() -> None:
    # Толщины штатных проставок: Shimano кладёт 1.8 мм, SRAM для шоссейных
    # Red/Force/Rival AXS — 2.8 мм.
    assert model_number("shimano_thickness") == 1.8
    assert model_number("sram_thickness") == 2.8


def test_spacer_tongue_is_stepped_thin_end_first() -> None:
    # Тонкий конец идёт первым: им проставка находит щель Shimano, а целиком
    # язычок садится в более широкий зазор SRAM.
    assert model_number("shimano_thickness") < model_number("sram_thickness")
    assert model_number("spacer_thin_length") < model_number("spacer_tongue_length")
    assert model_number("spacer_label_depth") < model_number("shimano_thickness")


def test_spacer_tongue_reaches_the_pads() -> None:
    # Язычок должен выйти за кромку медали настолько, чтобы перекрыть колодку.
    stick_out = model_number("spacer_tongue_length") - 3
    assert stick_out > 12, f"язычок торчит всего на {stick_out:.1f} мм"
    assert model_number("spacer_tongue_width") < 16, "шире щели для ротора не пролезет"


def model_string(name: str) -> str:
    """Строковый параметр модели."""
    match = re.search(rf'^{name} = "(.*)";', MODEL_PATH.read_text(encoding="utf-8"), re.M)
    assert match is not None, f"в модели нет параметра {name}"
    return match.group(1)


def test_engraved_lines_fit_inside_the_rim() -> None:
    # Надписи идут прямыми строками по хорде: за краем диска они бы обрезались.
    radius = model_number("medal_diameter") / 2
    size = model_number("text_size")
    for name, y_name in (("title_line", "title_y"), ("role_line", "role_y")):
        line = model_string(name)
        y = model_number(y_name)
        width = text_width(line, SANS_BOLD, size / ASCENT)
        chord = 2 * math.sqrt(radius**2 - y**2)
        assert width < chord - 4, f"«{line}» шире хорды: {width:.1f} против {chord:.1f} мм"


def test_engraving_says_the_same_as_the_trophy() -> None:
    assert model_string("title_line") == f"{RACE.short_title} · {RACE.date_numeric}"
    assert "Участник" in model_string("role_line")


def test_key_driver_sticks_out_of_the_medal() -> None:
    # Шлицы у крышки внутренние, поэтому ключ — выступ, а не гнездо.
    assert model_number("cap_points") == 8
    assert model_number("cap_driver_height") >= 6, "короткий выступ выскочит из шлицев"
    assert model_number("cap_lead_in") > 0, "без заходной фаски ключ не наденется"


def test_key_driver_leaves_the_engraving_alone() -> None:
    # Выступ стоит в центре, надписи идут выше и ниже него.
    outer = model_number("cap_root_diameter") / 2 + model_number("cap_tooth_height")
    lowest_line = model_number("role_y") - model_number("text_size") / 2
    assert lowest_line > outer, "нижняя строка упирается в шлицы"


def test_two_whistles_differ_in_pitch() -> None:
    # Камера меньше — тон выше: собачий свисток пронзительнее обычного.
    assert model_number("dog_chamber_diameter") < model_number("whistle_chamber_diameter")


def test_whistle_cavity_stays_inside_the_medal() -> None:
    wall = model_number("whistle_wall")
    chamber = model_number("whistle_chamber_height")
    assert wall + chamber < model_number("medal_thickness"), "камера пробила бы медаль"
    assert model_number("whistle_chamber_diameter") < model_number("medal_diameter") / 2


def test_whistle_channel_is_printable_without_supports() -> None:
    # Канал перекрывается мостом: шире 6 мм он бы провис.
    assert model_number("whistle_channel_width") <= 6
    assert model_number("whistle_channel_height") >= 0.8, "тоньше не продуется"


def test_lanyard_hole_does_not_break_the_rim() -> None:
    margin = model_number("lanyard_margin")
    assert margin > model_number("lanyard_hole") / 2, "отверстие вышло бы за кромку"
