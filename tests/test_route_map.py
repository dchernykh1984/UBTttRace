"""Проверки карты трассы для партнёров."""

from pathlib import Path

from PIL import Image

from ubt_race_docs.cli import main
from ubt_race_docs.route_map import (
    DISTANCE_KM,
    GIANT_BLUE,
    HEIGHT,
    TOTAL_ASCENT_M,
    TURN_KM,
    WIDTH,
    elevation_at,
    render,
)


def test_map_is_rendered_at_the_declared_size(tmp_path: Path) -> None:
    path = render(tmp_path / "map.png")
    with Image.open(path) as image:
        assert image.size == (WIDTH, HEIGHT)
        assert image.format == "PNG"


def test_route_goes_down_to_the_turn_and_back_up() -> None:
    # Трасса «туда и обратно»: разворот в низшей точке, финиш на высоте старта.
    assert elevation_at(0) > elevation_at(TURN_KM)
    assert elevation_at(DISTANCE_KM) == elevation_at(0)
    lowest = min(elevation_at(step / 10) for step in range(int(DISTANCE_KM * 10) + 1))
    assert abs(elevation_at(TURN_KM) - lowest) < 1


def test_profile_matches_the_ascent_from_the_track() -> None:
    step = 0.01
    steps = int(DISTANCE_KM / step)
    gain = sum(
        max(0.0, elevation_at((index + 1) * step) - elevation_at(index * step))
        for index in range(steps)
    )
    assert abs(gain - TOTAL_ASCENT_M) < 2, f"набор {gain:.1f} м вместо {TOTAL_ASCENT_M}"


def test_map_is_painted_in_the_partner_colour(tmp_path: Path) -> None:
    # Карта делается под макеты партнёра, поэтому его синий должен занимать
    # заметную часть кадра: нитка трассы, цифры, профиль.
    with Image.open(render(tmp_path / "map.png")) as image:
        colours = image.convert("RGB").getcolors(maxcolors=1 << 24) or []
    blue = sum(count for count, colour in colours if colour == GIANT_BLUE)
    assert blue > 20_000, f"синего партнёра всего {blue} пикселей"


def test_cli_draws_the_map(tmp_path: Path) -> None:
    assert main(["map", "--out", str(tmp_path)]) == 0
    assert (tmp_path / "map.png").is_file()
