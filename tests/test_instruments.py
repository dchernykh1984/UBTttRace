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


def test_every_instrument_is_cut_into_its_own_file() -> None:
    plan = {task.filename: task for task in render_plan()}
    assert set(plan) == {f"tool-{kind}.stl" for kind, _ in KINDS}


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


def test_engraving_keeps_clear_of_the_working_edges() -> None:
    # У измерителя щупы на торцах: до X = 5 и после X = 140 трогать нельзя.
    for name in ("chain_text_at", "chain_logo_at", "chain_giant_at"):
        x, _ = model_point(name)
        assert 10 < x < 135, f"{name}: гравировка заходит на рабочую часть, X={x}"
