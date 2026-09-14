"""Проверки инструментов гонки."""

import re

from ubt_race_docs.instruments import KINDS, MODEL_PATH, VENDOR_DIR, render_plan

ASCENT = 0.72
"""Доля em, по которой OpenSCAD отмеряет `size` у текста в DejaVu."""


def source() -> str:
    return MODEL_PATH.read_text(encoding="utf-8")


def model_number(name: str) -> float:
    match = re.search(rf"^{name} = (-?[0-9.]+);", source(), re.M)
    assert match is not None, f"в модели нет параметра {name}"
    return float(match.group(1))


def model_point(name: str) -> tuple[float, float]:
    """Координаты `[x, y]` из параметра модели."""
    match = re.search(rf"^{name} = \[(-?[0-9.]+), *(-?[0-9.]+)\];", source(), re.M)
    assert match is not None, f"в модели нет параметра {name}"
    return float(match.group(1)), float(match.group(2))


def model_line(name: str) -> str:
    match = re.search(rf'^{name} = "(.*)";', source(), re.M)
    assert match is not None, f"в модели нет параметра {name}"
    return match.group(1)


def model_numbers(name: str) -> list[float]:
    match = re.search(rf"^{name} = \[([-0-9.,\s]*)\];", source(), re.M)
    assert match is not None, f"в модели нет параметра {name}"
    return [float(v) for v in match.group(1).split(",")]


def chain_span(wear: float) -> float:
    """Пролёт между внешними гранями пары щупов для заданного износа."""
    links = model_number("chain_links")
    pitch = model_number("chain_pitch")
    return links * pitch * (1 + wear / 100) - model_number("chain_roller")


def test_vendor_models_are_shipped() -> None:
    assert (VENDOR_DIR / "cassette-cleaner.stl").is_file(), "нет исходной модели скребка"


def test_vendor_licences_are_documented() -> None:
    # Формы рисовали не мы: источник и лицензия должны быть названы рядом.
    readme = (VENDOR_DIR / "README.md").read_text(encoding="utf-8")
    assert "CC BY 4.0" in readme
    assert "printables.com" in readme
    # И там же сказано, почему двух моделей здесь нет.
    assert "CC BY-NC" in readme


def test_files_are_named_like_the_other_medals() -> None:
    # Для участника это такая же награда, только другой формы.
    assert all(task.filename.startswith("medal-") for task in render_plan())


def test_every_instrument_is_cut_into_its_own_file() -> None:
    plan = {task.filename: task for task in render_plan()}
    assert set(plan) == {f"medal-{kind}.stl" for kind, _ in KINDS}


def test_model_handles_every_kind() -> None:
    for kind, _ in KINDS:
        assert f'part == "{kind}"' in source()


def test_engraving_does_not_weaken_the_tools() -> None:
    # Гравировка снимает не больше четверти толщины: иначе измеритель
    # сломается пополам, а скребок согнётся о звёзды.
    for tool in ("chain", "cassette"):
        depth = model_number(f"{tool}_engrave")
        thickness = model_number(f"{tool}_thickness")
        assert depth < thickness / 4, f"{tool}: гравировка {depth} мм при толщине {thickness}"


def test_gauge_measures_a_real_chain() -> None:
    # Цепь у всех шоссейных трансмиссий одна и та же: шаг полдюйма,
    # ролик ⌀7.75. От этих двух цифр и считается пролёт между щупами.
    assert model_number("chain_pitch") == 12.7
    assert 7.5 <= model_number("chain_roller") <= 8.0
    marks = model_numbers("chain_marks")
    assert marks == [0.5, 1.0], "метки износа: 0.5 % для 11–12 скоростей и 1.0 % для старых"
    for wear in marks:
        expected = model_number("chain_links") * 12.7 * (1 + wear / 100) - model_number(
            "chain_roller"
        )
        assert abs(chain_span(wear) - expected) < 1e-9


def test_gauge_teeth_land_in_the_same_kind_of_gap() -> None:
    # Просветы между роликами чередуются: узкие между внутренними пластинами
    # и широкие между внешними. Чтобы оба щупа попадали в одинаковые,
    # между ними должно быть нечётное число шагов.
    assert model_number("chain_links") % 2 == 1


def test_gauge_tooth_enters_the_gap() -> None:
    pitch = model_number("chain_pitch")
    roller = model_number("chain_roller")
    tooth = model_number("chain_tooth")
    assert tooth < pitch - roller, "щуп толще просвета новой цепи — не войдёт никогда"
    # Дальний щуп стоит в своём просвете: слева ролик, справа следующий.
    for wear in model_numbers("chain_marks"):
        worn = pitch * (1 + wear / 100)
        far = chain_span(wear)
        assert far - tooth >= (model_number("chain_links") - 1) * worn, "щуп сел не в тот просвет"
    # Между внутренними пластинами 12-скоростной цепи около 2.2 мм.
    assert model_number("chain_tooth_thickness") <= 2.2
    # Пластины цепи высотой около 11 мм, и спинка упирается в их кромку.
    # Ролики щуп задевает своей прямой частью, а не сужением у кончика:
    # иначе он коснулся бы их выше самого широкого места и соврал.
    flat = model_number("chain_tooth_reach") - model_number("chain_tooth_lead")
    assert flat > 11 / 2, "прямая часть щупа не достаёт до оси ролика"


def test_gauge_is_stiff() -> None:
    # Прежний покупной измеритель был 2 мм толщиной и гнулся в руках,
    # из-за чего показывал что попало.
    assert model_number("chain_thickness") >= 5


def test_gauge_text_is_stacked_and_clear_of_the_partner() -> None:
    # Две строки стоят столбиком по одной оси, партнёр — справа от них.
    from ubt_race_docs.fonts import SANS_BOLD, text_width

    text_x, text_y = model_point("chain_text_at")
    role_x, role_y = model_point("chain_role_at")
    giant_x, giant_y = model_point("chain_giant_at")
    assert text_x == role_x, "строки не выровнены друг под другом"
    assert text_y > role_y, "участник должен стоять под гонкой"
    assert giant_y == 0, "партнёр не на середине спинки"

    def half(name: str, size: str) -> float:
        return text_width(model_line(name), SANS_BOLD, model_number(size) / ASCENT) / 2

    half_giant = model_number("chain_giant_width") / 2
    for name, size in (("title_line", "chain_text_size"), ("role_line", "chain_role_size")):
        assert text_x + half(name, size) < giant_x - half_giant, "строка налезает на партнёра"


def test_gauge_says_the_same_as_the_medal() -> None:
    # На измерителе то же самое, что на медали: гонка и кого награждаем.
    assert "Участник" in model_line("role_line")


def test_gauge_marks_stand_by_their_own_teeth() -> None:
    # Проценты подписаны у той кромки, чьи щупы их меряют, — иначе
    # инструментом не пользоваться.
    mark_x, mark_y = model_point("chain_mark_at")
    assert mark_y > 0, "метка должна стоять у кромки, а не по середине"
    assert mark_y + model_number("chain_mark_size") * 1.35 / 2 < model_number("chain_spine") / 2
    assert abs(mark_x - chain_span(1.0)) < 10, "метка стоит не у своих щупов"


def test_cassette_is_engraved_on_the_clean_side() -> None:
    # Лицевую занимает авторская надпись, поэтому гравируем обратную сторону.
    assert "module back_engraving()" in source()
    assert "mirror([1, 0, 0])" in source(), "на обороте надписи надо зеркалить"
    # Читают надписи с обратной стороны, поэтому в модели порядок обратный:
    # партнёр слева, надписи справа.
    giant_x, _ = model_point("cassette_giant_at")
    title_x, _ = model_point("cassette_title_at")
    assert giant_x < title_x, "порядок элементов сбился"


def test_tools_carry_no_team_emblem() -> None:
    # Эмблему убрали со всех медалей: мелких деталей в ней столько,
    # что на печати выходит каша.
    assert "ubt-logo" not in source(), "эмблема вернулась на инструменты"
