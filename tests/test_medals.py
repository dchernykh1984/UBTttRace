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


def test_jockey_slot_matches_a_derailleur_tooth() -> None:
    # Прорезь под зуб ролика 12-скоростной трансмиссии: он около 2 мм шириной,
    # прорезь чуть шире, чтобы заходила по грязи.
    width = model_number("jockey_slot_width")
    assert 2.4 < width < 3.4, f"прорезь {width} мм не сядет на зуб ролика"
    assert model_number("jockey_slot_depth") > 5, "мелкая прорезь не достанет до впадины"
    assert model_number("jockey_notch") < model_number("jockey_slot_depth")


def test_jockey_slot_misses_the_engraving() -> None:
    # Прорезь режет медаль насквозь: сверху она развалила бы эмблему,
    # по горизонтали — перерезала бы строки.
    import math

    direction = model_number("jockey_direction")
    radius = model_number("medal_diameter") / 2
    depth = model_number("jockey_slot_depth")
    # самая глубокая точка прорези
    x = -(radius - depth) * math.sin(math.radians(direction))
    y = (radius - depth) * math.cos(math.radians(direction))
    logo_half = model_number("logo_height") * 99.95 / 116.1 / 2
    assert abs(x) > logo_half + model_number("jockey_slot_width"), "прорезь заденет эмблему"
    for line_y in (model_number("title_y"), model_number("role_y")):
        assert abs(y - line_y) > model_number("text_size"), "прорезь заденет строку"


def test_jockey_edge_is_thin_enough_for_the_cage() -> None:
    # Между щёчками рамки переключателя пятимиллиметровым диском не подлезть.
    edge = model_number("jockey_edge_thickness")
    assert edge < 2.2, f"рабочая кромка {edge} мм не войдёт в рамку"
    assert edge > 1.0, "тоньше миллиметра кромка сломается о зуб"
    assert model_number("jockey_edge_reach") > model_number("jockey_slot_depth")


def test_key_driver_sticks_out_of_the_medal() -> None:
    # Шлицы у крышки внутренние, поэтому ключ — выступ, а не гнездо.
    assert model_number("cap_points") == 8, "зубцов столько же, сколько у заводского"
    assert model_number("cap_driver_height") >= 6, "короткий выступ выскочит из шлицев"
    # Размеры сняты с готовых моделей настоящих ключей.
    assert 15.0 < model_number("cap_outer_diameter") < 15.8
    assert 1.0 <= model_number("cap_groove_depth") <= 1.8
    assert model_number("cap_lead_in") > 0, "без заходной фаски ключ не наденется"


def test_key_teeth_are_wide_with_round_grooves() -> None:
    # У заводского ключа зубцы широкие, а впадины между ними узкие
    # и круглые — строим их вычитанием цилиндров, а не наращиванием.
    source = MODEL_PATH.read_text(encoding="utf-8")
    assert "cylinder(d = cap_groove_width" in source
    groove_arc = model_number("cap_groove_width")
    tooth_arc = 3.1416 * model_number("cap_outer_diameter") / model_number("cap_points")
    assert groove_arc < tooth_arc, "впадина шире зуба — профиль вывернут наизнанку"
    # Впадины у заводского ключа мелкие: глубокие срезали бы зубцы крышки.
    assert model_number("cap_groove_depth") < model_number("cap_outer_diameter") / 10


def test_face_elements_do_not_overlap() -> None:
    # Раскладка лица сверху вниз: эмблема, гонка, роль, партнёр.
    radius = model_number("medal_diameter") / 2
    size = model_number("text_size")
    logo_top = model_number("logo_y") + model_number("logo_height") / 2
    logo_bottom = model_number("logo_y") - model_number("logo_height") / 2
    title_top = model_number("title_y") + size / 2
    title_bottom = model_number("title_y") - size / 2
    role_top = model_number("role_y") + size / 2
    assert logo_top < radius - 3, "эмблема упирается в кромку"
    assert logo_bottom > title_top, "эмблема налезает на строку гонки"
    assert title_bottom > role_top, "строки налезают друг на друга"
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


def test_lanyard_hole_clears_the_engraving() -> None:
    # Отверстие стоит на 45°, и ни строки, ни эмблема в него не упираются.
    import math

    offset = model_number("medal_diameter") / 2 - model_number("lanyard_margin")
    x = offset * math.cos(math.radians(45))
    y = offset * math.sin(math.radians(45))
    edge = model_number("lanyard_hole") / 2 + 1
    logo_half = model_number("logo_height") * 99.95 / 116.1 / 2
    assert x - edge > logo_half, "отверстие задевает эмблему"
    for line_y in (model_number("title_y"), model_number("role_y")):
        assert y - edge > line_y + model_number("text_size") / 2, "отверстие задевает строку"
