"""Отступы гравировки до кромки детали.

Проверка растёт из ошибки: надписи не раз вылезали за край или садились
на чужую гравировку, а на рендере это было видно не всегда. Здесь отступ
считается по контуру исходной модели — той, на которую мы гравируем.
"""

import math
import re
import struct
from pathlib import Path

from ubt_race_docs.fonts import SANS_BOLD, text_width
from ubt_race_docs.instruments import MODEL_PATH, VENDOR_DIR

ASCENT = 0.72
"""Доля em, по которой OpenSCAD отмеряет `size` у текста в DejaVu.

Цифра нарочно занижена: по textmetrics самого OpenSCAD отношение лежит
между 0.726 и 0.741 в зависимости от строки, а так оценка ширины всегда
получается с запасом, и проверка не пропустит надпись, которая на самом
деле шире.
"""

GIANT_ASPECT = 308 / 1600
"""Высота логотипа партнёра относительно его ширины."""

MIN_MARGIN = 2.0
"""Минимальный зазор между гравировкой и кромкой, мм."""


def source() -> str:
    return MODEL_PATH.read_text(encoding="utf-8")


def number(name: str) -> float:
    match = re.search(rf"^{name} = ([\d.-]+);", source(), re.M)
    assert match is not None, f"в модели нет параметра {name}"
    return float(match.group(1))


def point(name: str) -> tuple[float, float]:
    match = re.search(rf"^{name} = \[(-?[\d.]+), *(-?[\d.]+)\];", source(), re.M)
    assert match is not None, f"в модели нет параметра {name}"
    return float(match.group(1)), float(match.group(2))


def line(name: str) -> str:
    match = re.search(rf'^{name} = "(.*)";', source(), re.M)
    assert match is not None, f"в модели нет параметра {name}"
    return match.group(1)


Triangle = tuple[tuple[float, ...], tuple[float, ...], tuple[float, ...]]
Segment = tuple[tuple[float, float], tuple[float, float]]
Box = tuple[float, float, float, float]


def triangles(path: Path) -> list[Triangle]:
    data = path.read_bytes()
    count = struct.unpack("<I", data[80:84])[0]
    out: list[Triangle] = []
    for index in range(count):
        offset = 84 + index * 50 + 12
        values = struct.unpack("<9f", data[offset : offset + 36])
        out.append((values[0:3], values[3:6], values[6:9]))
    return out


def outline(path: Path, z: float) -> list[Segment]:
    """Контур детали на высоте `z` — набор отрезков в плоскости XY."""
    segments: list[Segment] = []
    for tri in triangles(path):
        heights = [v[2] - z for v in tri]
        if all(h > 0 for h in heights) or all(h < 0 for h in heights):
            continue
        crossings: list[tuple[float, float]] = []
        for a, b in ((0, 1), (1, 2), (2, 0)):
            first, second = heights[a], heights[b]
            if first == second:
                continue
            if (first <= 0 <= second) or (second <= 0 <= first):
                t = first / (first - second)
                crossings.append(
                    (
                        tri[a][0] + t * (tri[b][0] - tri[a][0]),
                        tri[a][1] + t * (tri[b][1] - tri[a][1]),
                    )
                )
        if len(crossings) >= 2:
            segments.append((crossings[0], crossings[1]))
    return segments


def probes(box: Box, angle: float) -> list[tuple[float, float]]:
    """Углы, середины сторон и центр надписи, повёрнутой вдоль детали."""
    cx, cy, width, height = box
    cos, sin = math.cos(math.radians(angle)), math.sin(math.radians(angle))
    return [
        (cx + u * cos - v * sin, cy + u * sin + v * cos)
        for u in (-width / 2, 0.0, width / 2)
        for v in (-height / 2, 0.0, height / 2)
    ]


def is_inside(px: float, py: float, segments: list[Segment]) -> bool:
    """Точка внутри детали? Без этого надпись «помещается» и в вырезе."""
    crossings = 0
    for (ax, ay), (bx, by) in segments:
        if (ay > py) != (by > py) and ax + (py - ay) / (by - ay) * (bx - ax) > px:
            crossings += 1
    return crossings % 2 == 1


def margin(box: Box, segments: list[Segment], angle: float = 0.0) -> float:
    """Наименьшее расстояние от надписи до кромки; со знаком минус — вне детали."""
    best = float("inf")
    points = probes(box, angle)
    for px, py in points:
        for (ax, ay), (bx, by) in segments:
            dx, dy = bx - ax, by - ay
            length = dx * dx + dy * dy
            t = 0.0 if length == 0 else ((px - ax) * dx + (py - ay) * dy) / length
            t = min(1.0, max(0.0, t))
            best = min(best, math.hypot(px - (ax + t * dx), py - (ay + t * dy)))
    if not all(is_inside(px, py, segments) for px, py in points):
        return -best
    return best


def no_overlaps(boxes: dict[str, Box], angle: float = 0.0) -> None:
    """Ни одна надпись не должна налезать на соседнюю."""
    cos, sin = math.cos(math.radians(angle)), math.sin(math.radians(angle))
    along = {
        name: (cx * cos + cy * sin, -cx * sin + cy * cos, w, h)
        for name, (cx, cy, w, h) in boxes.items()
    }
    names = list(along)
    for first in range(len(names)):
        for second in range(first + 1, len(names)):
            u1, v1, w1, h1 = along[names[first]]
            u2, v2, w2, h2 = along[names[second]]
            apart = abs(u1 - u2) >= (w1 + w2) / 2 or abs(v1 - v2) >= (h1 + h2) / 2
            assert apart, f"{names[first]} налезает на {names[second]}"


def chain_boxes() -> dict[str, Box]:
    size = number("chain_text_size")
    mark = number("chain_mark_size")
    mark_x, mark_y = point("chain_mark_at")
    return {
        "гонка": (
            *point("chain_text_at"),
            text_width(line("title_line"), SANS_BOLD, size / ASCENT),
            size * 1.35,
        ),
        "партнёр": (
            *point("chain_giant_at"),
            number("chain_giant_width"),
            number("chain_giant_width") * GIANT_ASPECT,
        ),
        "метка 0.5": (
            mark_x,
            mark_y,
            text_width("0,5 %", SANS_BOLD, mark / ASCENT),
            mark * 1.35,
        ),
        "метка 1.0": (
            mark_x,
            -mark_y,
            text_width("1,0 %", SANS_BOLD, mark / ASCENT),
            mark * 1.35,
        ),
    }


def test_gauge_engraving_stays_on_the_spine() -> None:
    # Спинка измерителя — прямоугольник, поэтому отступы считаются прямо:
    # гравировка не должна подходить к её краям ближе двух миллиметров.
    half = number("chain_spine") / 2
    tail = number("chain_tail")
    span = number("chain_links") * number("chain_pitch") * 1.01 - number("chain_roller")
    for label, (cx, cy, width, height) in chain_boxes().items():
        left, right = cx - width / 2, cx + width / 2
        top, bottom = cy + height / 2, cy - height / 2
        assert left > -tail + MIN_MARGIN, f"{label}: вылезает за левый торец"
        assert right < span + tail - MIN_MARGIN, f"{label}: вылезает за правый торец"
        assert top < half - 1.0, f"{label}: подходит к верхней кромке"
        assert bottom > -half + 1.0, f"{label}: подходит к нижней кромке"


def test_gauge_engraving_does_not_collide() -> None:
    no_overlaps(chain_boxes())


def test_cassette_engraving_keeps_its_distance() -> None:
    segments = outline(VENDOR_DIR / "cassette-cleaner.stl", 0.2)
    size = number("cassette_text_size")
    angle = number("cassette_angle")
    boxes = {
        "гонка": (
            *point("cassette_title_at"),
            text_width(line("title_line"), SANS_BOLD, size / ASCENT),
            size * 1.35,
        ),
        "участник": (
            *point("cassette_role_at"),
            text_width(line("role_line"), SANS_BOLD, size / ASCENT),
            size * 1.35,
        ),
        "партнёр": (
            *point("cassette_giant_at"),
            number("cassette_giant_width"),
            number("cassette_giant_width") * GIANT_ASPECT,
        ),
    }
    for label, box in boxes.items():
        gap = margin(box, segments, angle)
        assert gap > 0, f"{label}: вышел за деталь или сел на вырез"
        assert gap > MIN_MARGIN, f"{label}: до кромки всего {gap:.1f} мм"
    no_overlaps(boxes, angle)


def centre_of(segments: list[Segment], x: float) -> float:
    """Середина детали по высоте в сечении `x`."""
    heights = []
    for (ax, ay), (bx, by) in segments:
        if ax != bx and (ax - x) * (bx - x) <= 0:
            heights.append(ay + (x - ax) / (bx - ax) * (by - ay))
    assert heights, f"в сечении X={x} нет детали"
    return (min(heights) + max(heights)) / 2


def test_cassette_engraving_follows_the_centre_line() -> None:
    # Деталь сужается наискось: одинаковый Y у всех элементов означал бы,
    # что один жмётся к верхней кромке, другой к нижней.
    segments = outline(VENDOR_DIR / "cassette-cleaner.stl", 0.2)
    x, y = point("cassette_giant_at")
    drift = abs(y - centre_of(segments, x))
    assert drift < 1.5, f"партнёр сидит на {drift:.1f} мм в стороне от середины"
    # Надписи идут парой вокруг середины.
    title_x, title_y = point("cassette_title_at")
    _, role_y = point("cassette_role_at")
    middle = centre_of(segments, title_x)
    assert abs((title_y + role_y) / 2 - middle) < 1.5, "пара строк съехала с середины"
