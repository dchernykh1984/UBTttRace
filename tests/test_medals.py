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


def test_spacers_point_in_opposite_directions() -> None:
    # Язычков два, в разные стороны: тонкий под Shimano, толстый под SRAM.
    source = MODEL_PATH.read_text(encoding="utf-8")
    assert "spacer_tongue(shimano_thickness, 0)" in source
    assert "spacer_tongue(sram_thickness, 180)" in source
    assert model_number("shimano_thickness") < model_number("sram_thickness")
    assert model_number("spacer_label_depth") < model_number("shimano_thickness")


def test_spacer_tongue_holds_itself_in_the_caliper() -> None:
    # Без заусенцев проставка вылетает из суппорта на первой же кочке.
    barb = model_number("spacer_barb")
    assert barb > 0.2, "заусенец меньше сопла не напечатается"
    assert barb < 1, "слишком крупный заусенец не даст вставить язычок"
    assert model_number("spacer_barb_at") < model_number("spacer_tongue_length")


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


def test_key_teeth_are_wide_with_round_grooves() -> None:
    # У заводского ключа зубцы широкие, а впадины между ними узкие
    # и круглые — строим их вычитанием цилиндров, а не наращиванием.
    source = MODEL_PATH.read_text(encoding="utf-8")
    assert "cylinder(d = cap_groove_width" in source
    groove_arc = model_number("cap_groove_width")
    tooth_arc = 3.1416 * model_number("cap_outer_diameter") / model_number("cap_points")
    assert groove_arc < tooth_arc / 2, "впадина шире зуба — профиль вывернут наизнанку"


def test_face_elements_do_not_overlap() -> None:
    # Раскладка лица: гонка, эмблема, роль, партнёр — сверху вниз, без наложений.
    radius = model_number("medal_diameter") / 2
    title_bottom = model_number("title_y") - model_number("text_size") / 2
    logo_top = model_number("logo_y") + model_number("logo_height") / 2
    logo_bottom = model_number("logo_y") - model_number("logo_height") / 2
    role_top = model_number("role_y") + (model_number("text_size") + 0.3) / 2
    assert title_bottom > logo_top, "заголовок налезает на эмблему"
    assert logo_bottom > role_top, "эмблема налезает на строку участника"
    assert model_number("title_y") + model_number("text_size") < radius - 2
    assert abs(model_number("giant_y")) + 3 < radius - 2


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
