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

ASCENT = 0.7598
"""Доля em, по которой OpenSCAD отмеряет `size` у текста в DejaVu."""

UBT_ASPECT = 99.95 / 116.1
"""Ширина логотипа команды относительно его высоты."""

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


def margin(box: tuple[float, float, float, float], segments: list[Segment]) -> float:
    """Наименьшее расстояние от углов надписи до кромки детали."""
    cx, cy, width, height = box
    corners = [(cx + sx * width / 2, cy + sy * height / 2) for sx in (-1, 1) for sy in (-1, 1)]
    best = float("inf")
    for px, py in corners:
        for (ax, ay), (bx, by) in segments:
            dx, dy = bx - ax, by - ay
            length = dx * dx + dy * dy
            t = 0.0 if length == 0 else ((px - ax) * dx + (py - ay) * dy) / length
            t = min(1.0, max(0.0, t))
            best = min(best, math.hypot(px - (ax + t * dx), py - (ay + t * dy)))
    return best


def no_overlaps(boxes: dict[str, tuple[float, float, float, float]]) -> None:
    """Ни одна надпись не должна налезать на соседнюю."""
    names = list(boxes)
    for first in range(len(names)):
        for second in range(first + 1, len(names)):
            x1, y1, w1, h1 = boxes[names[first]]
            x2, y2, w2, h2 = boxes[names[second]]
            apart = abs(x1 - x2) >= (w1 + w2) / 2 or abs(y1 - y2) >= (h1 + h2) / 2
            assert apart, f"{names[first]} налезает на {names[second]}"


def test_ruler_engraving_keeps_its_distance() -> None:
    segments = outline(VENDOR_DIR / "chain-wear-indicator.stl", 1.8)
    size = number("chain_text_size")
    boxes = {
        "эмблема": (
            *point("chain_logo_at"),
            number("chain_logo_height") * UBT_ASPECT,
            number("chain_logo_height"),
        ),
        "строка": (
            *point("chain_text_at"),
            text_width(line("title_line"), SANS_BOLD, size / ASCENT),
            size,
        ),
        "партнёр": (
            *point("chain_giant_at"),
            number("chain_giant_width"),
            number("chain_giant_width") * GIANT_ASPECT,
        ),
    }
    for label, box in boxes.items():
        gap = margin(box, segments)
        assert gap > MIN_MARGIN, f"{label}: до кромки всего {gap:.1f} мм"
    no_overlaps(boxes)


def test_cassette_engraving_keeps_its_distance() -> None:
    segments = outline(VENDOR_DIR / "cassette-cleaner.stl", 0.2)
    size = number("cassette_text_size")
    boxes = {
        "эмблема": (
            *point("cassette_logo_at"),
            number("cassette_logo_height") * UBT_ASPECT,
            number("cassette_logo_height"),
        ),
        "гонка": (
            *point("cassette_title_at"),
            text_width(line("title_line"), SANS_BOLD, size / ASCENT),
            size,
        ),
        "участник": (
            *point("cassette_role_at"),
            text_width(line("role_line"), SANS_BOLD, size / ASCENT),
            size,
        ),
        "партнёр": (
            *point("cassette_giant_at"),
            number("cassette_giant_width"),
            number("cassette_giant_width") * GIANT_ASPECT,
        ),
    }
    for label, box in boxes.items():
        gap = margin(box, segments)
        assert gap > MIN_MARGIN, f"{label}: до кромки всего {gap:.1f} мм"
    no_overlaps(boxes)
