"""Проверки фона печатного листа."""

import tomllib
from pathlib import Path

import pytest
from pypdf import PdfReader
from reportlab.lib.units import mm
from reportlab.pdfgen.canvas import Canvas

from ubt_race_docs import background
from ubt_race_docs.background import (
    BACKGROUND_NAMES,
    BackgroundStyle,
    draw_background,
    draw_branded_background,
    resolve_image,
)
from ubt_race_docs.brand import LOGO_PATH

WIDTH = 210 * mm
HEIGHT = 297 * mm


def render(tmp_path: Path, name: str, image: Path | None) -> PdfReader:
    output = tmp_path / name
    canvas = Canvas(str(output), pagesize=(WIDTH, HEIGHT))
    draw_background(canvas, WIDTH, HEIGHT, image=image)
    canvas.showPage()
    canvas.save()
    return PdfReader(output)


def test_branded_background_puts_the_logo_watermark_on_the_page(tmp_path: Path) -> None:
    assert len(render(tmp_path, "branded.pdf", None).pages[0].images) == 1


def test_image_background_replaces_the_drawn_one(tmp_path: Path) -> None:
    reader = render(tmp_path, "image.pdf", LOGO_PATH)
    # Картинка одна — своего водяного знака фирменный фон уже не рисует.
    assert len(reader.pages[0].images) == 1


def test_background_stays_inside_the_printable_area() -> None:
    # Офисный принтер не печатает до края: фон отступает, иначе вылезет кайма.
    style = BackgroundStyle()
    assert style.safe_margin >= 4 * mm
    # Рамка должна пройти ниже полосы вместе с её чёрной отбивкой,
    # иначе горизонтальные стороны рамки не видно.
    assert style.frame_margin > style.safe_margin + style.band_height + style.band_rule


def test_watermark_is_faint_enough_to_write_over() -> None:
    assert 0 < BackgroundStyle().watermark_alpha <= 0.15


def test_background_draws_something(tmp_path: Path) -> None:
    empty = tmp_path / "empty.pdf"
    canvas = Canvas(str(empty), pagesize=(WIDTH, HEIGHT))
    canvas.showPage()
    canvas.save()

    filled = tmp_path / "filled.pdf"
    canvas = Canvas(str(filled), pagesize=(WIDTH, HEIGHT))
    draw_branded_background(canvas, WIDTH, HEIGHT)
    canvas.showPage()
    canvas.save()

    assert filled.stat().st_size > empty.stat().st_size


def test_no_image_by_default() -> None:
    assert resolve_image() is None


def test_explicit_image_wins(tmp_path: Path) -> None:
    picture = tmp_path / "фон.png"
    picture.write_bytes(LOGO_PATH.read_bytes())
    assert resolve_image(picture) == picture


def test_missing_image_is_reported(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="нет файла фона"):
        resolve_image(tmp_path / "нет-такого.png")


def test_image_dropped_into_the_assets_is_picked_up(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(background, "BACKGROUND_DIR", tmp_path)
    assert resolve_image() is None
    dropped = tmp_path / BACKGROUND_NAMES[0]
    dropped.write_bytes(LOGO_PATH.read_bytes())
    assert resolve_image() == dropped


def test_every_accepted_background_name_ships_with_the_package() -> None:
    # Иначе фон работает из исходников и молча пропадает из установленного пакета.
    pyproject = tomllib.loads(
        (Path(__file__).resolve().parents[1] / "pyproject.toml").read_text(encoding="utf-8")
    )
    patterns = pyproject["tool"]["setuptools"]["package-data"]["ubt_race_docs"]
    for name in BACKGROUND_NAMES:
        assert f"assets/backgrounds/*{Path(name).suffix}" in patterns
