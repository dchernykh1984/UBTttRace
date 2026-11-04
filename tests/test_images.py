"""Логотип команды лежит в двух видах — растр и вектор, — и они должны совпадать."""

import re

from PIL import Image

from ubt_race_docs.brand import LOGO_PATH

VECTOR_PATH = LOGO_PATH.with_suffix(".svg")


def test_vector_logo_sits_on_the_raster_canvas() -> None:
    # Вектор ставится вместо растра без перекладки: тот же квадрат, та же рамка.
    svg = VECTOR_PATH.read_text(encoding="utf-8")
    size = re.search(r'width="(\d+)" height="(\d+)"', svg)
    assert size is not None, "у вектора нет размера холста"
    assert tuple(map(int, size.groups())) == Image.open(LOGO_PATH).size


def test_vector_logo_has_the_raster_colour() -> None:
    # Сменили логотип и забыли перетрассировать — первым разъезжается цвет.
    fill = re.search(r'fill="#([0-9a-fA-F]{6})"', VECTOR_PATH.read_text(encoding="utf-8"))
    assert fill is not None, "у вектора нет заливки"
    raster = Image.open(LOGO_PATH).convert("RGBA")
    colours = raster.getcolors(raster.width * raster.height)
    assert colours is not None
    opaque = [(n, c[:3]) for n, c in colours if isinstance(c, tuple) and c[3] == 255]
    assert tuple(bytes.fromhex(fill.group(1))) == max(opaque)[1]
