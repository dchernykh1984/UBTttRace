"""Проверки медалей участникам."""

import math
import re
from itertools import pairwise

from ubt_race_docs.fonts import SANS_BOLD, text_width
from ubt_race_docs.medals import KINDS, MODEL_PATH, render_plan
from ubt_race_docs.race import RACE

ASCENT = 0.72
"""Доля em, по которой OpenSCAD отмеряет `size` у текста в DejaVu.

Цифра нарочно занижена: по textmetrics самого OpenSCAD отношение лежит
между 0.726 и 0.741 в зависимости от строки, а так оценка ширины всегда
получается с запасом.
"""

GIANT_ASPECT = 308 / 1600
"""Высота логотипа партнёра относительно его ширины."""

LINE_BOX = 1.35
"""Высота строки в долях кегля — с запасом на «Қ» и хвосты букв."""


def source() -> str:
    return MODEL_PATH.read_text(encoding="utf-8")


def model_number(name: str) -> float:
    """Числовой параметр модели — читаем прямо из .scad, чтобы не разъехалось."""
    match = re.search(rf"^{name} = (-?[0-9.]+);", source(), re.M)
    assert match is not None, f"в модели нет параметра {name}"
    return float(match.group(1))


def model_string(name: str) -> str:
    """Строковый параметр модели."""
    match = re.search(rf'^{name} = "(.*)";', source(), re.M)
    assert match is not None, f"в модели нет параметра {name}"
    return match.group(1)


def model_strings(name: str) -> list[str]:
    """Список строк — например, строки на лице медали."""
    match = re.search(rf"^{name} = \[(.*)\];", source(), re.M)
    assert match is not None, f"в модели нет параметра {name}"
    return re.findall(r'"([^"]*)"', match.group(1))


def model_numbers(name: str) -> list[float]:
    """Список чисел."""
    match = re.search(rf"^{name} = \[([-0-9.,\s]*)\];", source(), re.M)
    assert match is not None, f"в модели нет параметра {name}"
    return [float(v) for v in match.group(1).split(",")]


def face_boxes() -> dict[str, tuple[float, float, float]]:
    """Что стоит на лице медали: ширина, центр по Y, высота."""
    size = model_number("text_size")
    boxes = {
        text: (text_width(text, SANS_BOLD, size / ASCENT), y, size * LINE_BOX)
        for text, y in zip(model_strings("face_line"), model_numbers("face_y"), strict=True)
    }
    width = model_number("giant_width")
    boxes["партнёр"] = (width, model_number("giant_y"), width * GIANT_ASPECT)
    return boxes


def face_clearance(width: float, centre: float, height: float) -> float:
    """Запас элемента лица до кромки, отверстия под ленту и прорези скребка.

    Прорезь скребка режет медаль насквозь, поэтому она опасна и для лица:
    надпись она бы просто перерубила. Отверстие под ленту — тоже сквозное.
    """
    radius = model_number("medal_diameter") / 2
    half = width / 2
    top, bottom = centre + height / 2, centre - height / 2
    out = min(radius - 2.0 - math.hypot(half, y) for y in (top, bottom))

    hole = radius - model_number("lanyard_margin")
    hole_x = hole * math.cos(math.radians(45))
    keep = model_number("lanyard_hole") / 2 + 1.0
    dx = max(hole_x - half, 0.0)
    dy = 0.0 if bottom <= hole_x <= top else min(abs(hole_x - top), abs(hole_x - bottom))
    out = min(out, math.hypot(dx, dy) - keep)

    # прорезь идёт от кромки внутрь по диагонали: считаем расстояние до неё
    direction = math.radians(model_number("jockey_direction") + 90)
    unit = (math.cos(direction), math.sin(direction))
    inner = radius - model_number("jockey_slot_depth")
    slot_keep = model_number("jockey_slot_width") / 2 + 1.0
    for x in (-half, half):
        for y in (top, bottom):
            along = min(radius, max(inner, x * unit[0] + y * unit[1]))
            distance = math.hypot(x - along * unit[0], y - along * unit[1])
            out = min(out, distance - slot_keep)
    return out


def test_model_is_shipped_with_the_package() -> None:
    assert MODEL_PATH.is_file()
    assert "part" in source()


def test_every_kind_is_cut_into_its_own_file() -> None:
    plan = {task.filename: task for task in render_plan()}
    assert set(plan) == {f"medal-{kind}.stl" for kind, _ in KINDS}
    for task in plan.values():
        assert task.definitions == {}, "надписи медали зашиты в модель"


def test_model_handles_every_kind_we_ask_for() -> None:
    for kind, _ in KINDS:
        assert f'part == "{kind}"' in source(), f"модель не знает исполнения {kind}"


def test_medal_is_a_sixty_millimetre_disc() -> None:
    # Полсотни оказалось мало: на печати гравировка почти не читалась.
    assert model_number("medal_diameter") == 60
    assert model_number("medal_thickness") == 5


def test_engraving_is_deep_enough_to_read_after_printing() -> None:
    # Первый слой расплющивается, и мелкая гравировка заплывает.
    assert model_number("engrave_depth") >= 0.8
    assert model_number("text_size") >= 5.0


def test_face_has_no_team_emblem() -> None:
    # Эмблему убрали: мелких деталей в ней столько, что на печати каша.
    assert "ubt-logo" not in source(), "эмблема вернулась на медаль"


def test_every_face_element_fits_the_disc() -> None:
    # Строки идут хордами, а отверстие под ленту и прорезь скребка режут
    # медаль насквозь: всё это проверяется расчётом, а не на глаз.
    for label, (width, centre, height) in face_boxes().items():
        gap = face_clearance(width, centre, height)
        assert gap > 0, f"«{label}»: не помещается, не хватает {-gap:.1f} мм"


def test_engraving_says_the_same_as_the_trophy() -> None:
    lines = model_strings("face_line")
    assert lines[0] == RACE.short_title
    assert lines[1] == RACE.date_numeric
    assert "Участник" in lines


def test_jockey_slot_matches_a_derailleur_tooth() -> None:
    # Прорезь под зуб ролика 12-скоростной трансмиссии: он около 2 мм шириной,
    # прорезь чуть шире, чтобы заходила по грязи.
    width = model_number("jockey_slot_width")
    assert 2.4 < width < 3.4, f"прорезь {width} мм не сядет на зуб ролика"
    assert model_number("jockey_slot_depth") > 5, "мелкая прорезь не достанет до впадины"
    assert model_number("jockey_notch") < model_number("jockey_slot_depth")


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


def test_key_rim_is_knurled_for_grip() -> None:
    # Медалью крутят крышку, поэтому кромка рифлёная — шаг взят у заводского
    # ключа: 33 ребра на диаметре 40 мм, то есть примерно 3.8 мм по дуге.
    teeth = model_number("knurl_teeth")
    step = math.pi * model_number("medal_diameter") / teeth
    assert 3.0 < step < 4.6, f"шаг рифления {step:.1f} мм не похож на заводской"
    depth = model_number("knurl_depth")
    assert 0.4 < depth < 1.2, "слишком мелкое или слишком грубое рифление"
    assert depth < model_number("knurl_groove"), "канавка глубже своей ширины"


def test_key_teeth_are_wide_with_round_grooves() -> None:
    # У заводского ключа зубцы широкие, а впадины между ними узкие
    # и круглые — строим их вычитанием цилиндров, а не наращиванием.
    assert "cylinder(d = cap_groove_width" in source()
    groove_arc = model_number("cap_groove_width")
    tooth_arc = 3.1416 * model_number("cap_outer_diameter") / model_number("cap_points")
    assert groove_arc < tooth_arc, "впадина шире зуба — профиль вывернут наизнанку"
    # Впадины у заводского ключа мелкие: глубокие срезали бы зубцы крышки.
    assert model_number("cap_groove_depth") < model_number("cap_outer_diameter") / 10


def test_face_is_packed_without_wasted_space() -> None:
    # Свободное место на медали кончилось: между элементами не больше двух
    # миллиметров, иначе всё можно было сделать крупнее.
    for (upper, (_, upper_y, upper_h)), (lower, (_, lower_y, lower_h)) in pairwise(
        face_boxes().items()
    ):
        gap = (upper_y - upper_h / 2) - (lower_y + lower_h / 2)
        assert 0.5 < gap < 2.5, f"«{upper}» и «{lower}»: зазор {gap:.1f} мм"


def test_lanyard_hole_does_not_break_the_rim() -> None:
    margin = model_number("lanyard_margin")
    assert margin > model_number("lanyard_hole") / 2, "отверстие вышло бы за кромку"
