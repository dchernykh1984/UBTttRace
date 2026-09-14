"""Проверки брендированных инструментов гонки."""

import re

from ubt_race_docs.instruments import KINDS, MODEL_PATH, VENDOR_DIR, render_plan


def model_number(name: str) -> float:
    match = re.search(rf"^{name} = (-?[0-9.]+);", MODEL_PATH.read_text(encoding="utf-8"), re.M)
    assert match is not None, f"в модели нет параметра {name}"
    return float(match.group(1))


def test_vendor_models_are_shipped() -> None:
    for name in ("chain-wear-indicator.stl", "cassette-cleaner.stl"):
        assert (VENDOR_DIR / name).is_file(), f"нет исходной модели {name}"


def test_vendor_licences_are_documented() -> None:
    # Формы рисовали не мы: источник и лицензия должны быть названы рядом.
    readme = (VENDOR_DIR / "README.md").read_text(encoding="utf-8")
    assert "CC0" in readme and "CC BY 4.0" in readme
    assert "printables.com" in readme


def test_files_are_named_like_the_other_medals() -> None:
    # Для участника это такая же награда, только другой формы.
    assert all(task.filename.startswith("medal-") for task in render_plan())


def test_every_instrument_is_cut_into_its_own_file() -> None:
    plan = {task.filename: task for task in render_plan()}
    assert set(plan) == {f"medal-{kind}.stl" for kind, _ in KINDS}


def test_model_handles_every_kind() -> None:
    source = MODEL_PATH.read_text(encoding="utf-8")
    for kind, _ in KINDS:
        assert f'part == "{kind}"' in source


def test_engraving_does_not_weaken_the_tools() -> None:
    # Гравировка снимает не больше четверти толщины: иначе измеритель
    # сломается пополам, а скребок согнётся о звёзды.
    for tool in ("chain", "cassette"):
        depth = model_number(f"{tool}_engrave")
        thickness = model_number(f"{tool}_thickness")
        assert depth < thickness / 4, f"{tool}: гравировка {depth} мм при толщине {thickness}"


def model_point(name: str) -> tuple[float, float]:
    """Координаты `[x, y]` из параметра модели."""
    match = re.search(
        rf"^{name} = \[(-?[0-9.]+), *(-?[0-9.]+)\];",
        MODEL_PATH.read_text(encoding="utf-8"),
        re.M,
    )
    assert match is not None, f"в модели нет параметра {name}"
    return float(match.group(1)), float(match.group(2))


def model_line(name: str) -> str:
    match = re.search(rf'^{name} = "(.*)";', MODEL_PATH.read_text(encoding="utf-8"), re.M)
    assert match is not None, f"в модели нет параметра {name}"
    return match.group(1)


def test_ruler_engraving_sits_on_one_line_without_overlaps() -> None:
    # На планке всё выстроено по её середине: эмблема, строка, партнёр.
    from ubt_race_docs.fonts import SANS_BOLD, text_width

    ascent = 0.7598
    text_x, text_y = model_point("chain_text_at")
    logo_x, logo_y = model_point("chain_logo_at")
    giant_x, giant_y = model_point("chain_giant_at")
    assert text_y == logo_y == giant_y, "элементы не на одной линии"

    half_text = (
        text_width(model_line("title_line"), SANS_BOLD, model_number("chain_text_size") / ascent)
        / 2
    )
    half_logo = model_number("chain_logo_height") * 99.95 / 116.1 / 2
    half_giant = model_number("chain_giant_width") / 2
    assert logo_x + half_logo < text_x - half_text, "эмблема налезает на строку"
    assert text_x + half_text < giant_x - half_giant, "логотип партнёра налезает на дату"
    assert giant_x + half_giant < 140, "логотип партнёра уходит на щуп"


def test_cassette_is_engraved_on_the_clean_side() -> None:
    # Лицевую занимает авторская надпись, поэтому гравируем обратную сторону.
    source = MODEL_PATH.read_text(encoding="utf-8")
    assert "module back_engraving()" in source
    assert "mirror([1, 0, 0])" in source, "на обороте надписи надо зеркалить"
    # Читают надписи с обратной стороны, поэтому в модели порядок обратный:
    # партнёр слева, надписи в середине, эмблема справа.
    giant_x, _ = model_point("cassette_giant_at")
    title_x, _ = model_point("cassette_title_at")
    logo_x, _ = model_point("cassette_logo_at")
    assert giant_x < title_x < logo_x, "порядок элементов сбился"


def test_engraving_keeps_clear_of_the_working_edges() -> None:
    # У измерителя щупы на торцах: до X = 5 и после X = 140 трогать нельзя.
    for name in ("chain_text_at", "chain_logo_at", "chain_giant_at"):
        x, _ = model_point(name)
        assert 10 < x < 135, f"{name}: гравировка заходит на рабочую часть, X={x}"
