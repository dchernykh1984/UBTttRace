"""Карта трассы в стиле партнёра гонки.

Спонсорам нужна схема трассы под их макеты, поэтому карта нарисована кодом
в фирменных цветах Giant: синяя нитка маршрута, оранжевые акценты команды
и профиль высот под схемой. Растр, а не PDF: макетчику удобнее положить
картинку в баннер.

География схематична — это не топографическая карта, а схема: прямая дорога
из Кырбалтабая на северо-запад, разворот на половине и тот же путь обратно.
Цифры взяты из трека гонки (25 км, 55 м набора, перепад от 505 до 552 м).
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from .fonts import FONT_DIR
from .race import RACE

GIANT_BLUE = (45, 47, 147)
"""Синий с логотипа партнёра — им нарисована трасса."""

ORANGE = (240, 106, 30)
INK = (24, 26, 32)
MUTED = (122, 128, 140)
PAPER = (247, 248, 250)
PANEL = (238, 240, 244)
WATER = (176, 202, 226)
LAND = (231, 234, 238)
GREEN = (34, 160, 88)

WIDTH = 2400
HEIGHT = 1400

LOGO_DIR = Path(__file__).parent / "assets" / "images"


@dataclass(frozen=True)
class Landmark:
    """Село рядом с трассой: доля ширины, доля высоты, подпись."""

    x: float
    y: float
    name: str


LANDMARKS = (
    Landmark(0.905, 0.560, "Екпинди"),
    Landmark(0.955, 0.845, "Куш"),
    Landmark(0.430, 0.920, "Кайнар"),
    Landmark(0.205, 0.345, "Каратоган"),
)
"""Соседние сёла — по русской транслитерации со Strava."""

ELEVATION_KEYFRAMES: tuple[tuple[float, float], ...] = (
    (0.0, 552.0),
    (2.0, 546.0),
    (4.0, 541.5),
    (5.7, 540.0),
    (5.8, 531.0),
    (8.0, 524.0),
    (10.0, 517.0),
    (12.0, 507.0),
    (12.5, 505.0),
)
"""Профиль первой половины по треку; вторая половина — та же дорога назад."""

DISTANCE_KM = 25.0
TURN_KM = DISTANCE_KM / 2
TOTAL_ASCENT_M = 55
"""Набор высоты по треку — им же подобрана рябь профиля."""


def elevation_at(kilometre: float) -> float:
    """Высота на заданном километре: за разворотом профиль зеркальный."""
    position = kilometre if kilometre <= TURN_KM else DISTANCE_KM - kilometre
    previous_km, previous_height = ELEVATION_KEYFRAMES[0]
    for point_km, height in ELEVATION_KEYFRAMES[1:]:
        if position <= point_km:
            span = point_km - previous_km
            share = 0.0 if span == 0 else (position - previous_km) / span
            base = previous_height + (height - previous_height) * share
            # Дорога не идеально гладкая: мелкая рябь добавляет к перепаду
            # в 47 метров те восемь, из которых на треке набегает 55 набора.
            return base + 0.7 * math.sin(position * 3.1) + 0.44 * math.sin(position * 9.7)
        previous_km, previous_height = point_km, height
    return previous_height


@dataclass
class Fonts:
    """Начертания под растровую отрисовку."""

    title: ImageFont.FreeTypeFont = field(init=False)
    subtitle: ImageFont.FreeTypeFont = field(init=False)
    number: ImageFont.FreeTypeFont = field(init=False)
    label: ImageFont.FreeTypeFont = field(init=False)
    small: ImageFont.FreeTypeFont = field(init=False)
    tiny: ImageFont.FreeTypeFont = field(init=False)

    def __post_init__(self) -> None:
        bold = str(FONT_DIR / "DejaVuSans-Bold.ttf")
        regular = str(FONT_DIR / "DejaVuSans.ttf")
        condensed = str(FONT_DIR / "DejaVuSansCondensed-Bold.ttf")
        self.title = ImageFont.truetype(condensed, 92)
        self.subtitle = ImageFont.truetype(regular, 34)
        self.number = ImageFont.truetype(condensed, 66)
        self.label = ImageFont.truetype(bold, 30)
        self.small = ImageFont.truetype(regular, 26)
        self.tiny = ImageFont.truetype(regular, 22)


def paste_logo(canvas: Image.Image, name: str, box: tuple[int, int, int, int]) -> None:
    """Вписать логотип в прямоугольник, сохранив пропорции."""
    logo = Image.open(LOGO_DIR / name).convert("RGBA")
    left, top, right, bottom = box
    scale = min((right - left) / logo.width, (bottom - top) / logo.height)
    size = (max(1, round(logo.width * scale)), max(1, round(logo.height * scale)))
    resized = logo.resize(size, Image.Resampling.LANCZOS)
    position = (left + (right - left - size[0]) // 2, top + (bottom - top - size[1]) // 2)
    canvas.paste(resized, position, resized)


def draw_header(draw: ImageDraw.ImageDraw, canvas: Image.Image, fonts: Fonts) -> None:
    """Шапка: логотипы партнёра и команды, название и дата гонки.

    Плашка светлая: оба логотипа фирменные и на синем фоне потерялись бы —
    оранжевый потемнел бы, а синий Giant слился бы вовсе.
    """
    draw.rectangle((0, 0, WIDTH, 206), fill=(255, 255, 255))
    draw.rectangle((0, 206, WIDTH, 216), fill=GIANT_BLUE)
    paste_logo(canvas, "ubt-logo.png", (60, 26, 200, 166))
    draw.text((240, 44), "UBT TT 2026", font=fonts.title, fill=INK)
    draw.text(
        (246, 144),
        f"{RACE.date.ru} · {RACE.place.ru}",
        font=fonts.subtitle,
        fill=MUTED,
    )
    paste_logo(canvas, "giant-logo.png", (WIDTH - 470, 62, WIDTH - 70, 138))
    draw.text(
        (WIDTH - 470, 148),
        "Партнёр гонки · Жарыс серіктесі",
        font=fonts.tiny,
        fill=MUTED,
    )


def route_points() -> tuple[tuple[float, float], ...]:
    """Нитка трассы в долях кадра: юго-восток → излом → северо-запад."""
    return ((0.815, 0.815), (0.545, 0.470), (0.145, 0.130))


def map_position(share: float, box: tuple[int, int, int, int]) -> tuple[float, float]:
    """Точка на нитке по доле пройденного пути от старта до разворота."""
    left, top, right, bottom = box
    points = route_points()
    lengths = [math.dist(points[i], points[i + 1]) * 1.0 for i in range(len(points) - 1)]
    total = sum(lengths)
    walked = share * total
    for index, length in enumerate(lengths):
        if walked <= length or index == len(lengths) - 1:
            local = 0.0 if length == 0 else walked / length
            start, end = points[index], points[index + 1]
            x = start[0] + (end[0] - start[0]) * local
            y = start[1] + (end[1] - start[1]) * local
            return left + x * (right - left), top + y * (bottom - top)
        walked -= length
    raise AssertionError("недостижимо")


def draw_map_panel(draw: ImageDraw.ImageDraw, fonts: Fonts) -> None:
    """Схема трассы: дорога, соседние сёла, старт и разворот."""
    box = (60, 256, 1560, 1090)
    left, top, right, bottom = box
    draw.rounded_rectangle(box, radius=18, fill=LAND)

    # Речка западнее дороги — по ней схема узнаётся на местности.
    stream = [
        (
            left + (0.075 + 0.032 * math.sin(step / 3.4)) * (right - left),
            top + step / 20 * (bottom - top),
        )
        for step in range(21)
    ]
    draw.line(stream, fill=WATER, width=7, joint="curve")

    # Соседние дороги — тонкими штрихами, чтобы схема не висела в пустоте.
    for start, end in (((0.02, 0.62), (0.42, 0.99)), ((0.58, 0.05), (0.99, 0.42))):
        draw.line(
            [
                (left + start[0] * (right - left), top + start[1] * (bottom - top)),
                (left + end[0] * (right - left), top + end[1] * (bottom - top)),
            ],
            fill=(215, 218, 224),
            width=8,
        )

    track = [map_position(step / 60, box) for step in range(61)]
    draw.line(track, fill=(255, 255, 255), width=26, joint="curve")
    draw.line(track, fill=GIANT_BLUE, width=16, joint="curve")

    # Отметки ставим только на пути «туда»: назад та же дорога, и вторая
    # цифра на том же месте читалась бы как ошибка.
    for kilometre in (5, 10):
        x, y = map_position(kilometre / TURN_KM, box)
        draw.ellipse((x - 13, y - 13, x + 13, y + 13), fill=(255, 255, 255))
        draw.ellipse((x - 13, y - 13, x + 13, y + 13), outline=GIANT_BLUE, width=4)
        draw.text((x + 24, y - 16), f"{kilometre} км", font=fonts.tiny, fill=INK)

    turn_x, turn_y = map_position(1.0, box)
    draw.ellipse(
        (turn_x - 30, turn_y - 30, turn_x + 30, turn_y + 30),
        fill=(255, 255, 255),
        outline=GIANT_BLUE,
        width=8,
    )
    # Подписи над точкой: правее их перечеркнула бы сама нитка трассы.
    draw.text((turn_x + 46, turn_y - 88), "Разворот", font=fonts.label, fill=GIANT_BLUE)
    draw.text((turn_x + 46, turn_y - 50), "12,5 км · Бұрылыс", font=fonts.small, fill=MUTED)

    start_x, start_y = map_position(0.0, box)
    draw.ellipse(
        (start_x - 30, start_y - 30, start_x + 30, start_y + 30),
        fill=GREEN,
        outline=(255, 255, 255),
        width=8,
    )
    draw.text((start_x - 356, start_y - 52), "Старт · Финиш", font=fonts.label, fill=INK)
    draw.text((start_x - 356, start_y - 14), "Мәре · Старт", font=fonts.small, fill=MUTED)
    draw.text((start_x - 356, start_y + 22), "село Кырбалтабай", font=fonts.small, fill=MUTED)

    for landmark in LANDMARKS:
        x = left + landmark.x * (right - left)
        y = top + landmark.y * (bottom - top)
        draw.ellipse((x - 9, y - 9, x + 9, y + 9), fill=MUTED)
        draw.text((x + 20, y - 16), landmark.name, font=fonts.small, fill=MUTED)

    draw_compass(draw, (right - 110, top + 100), fonts)
    draw_scale_bar(draw, (left + 60, bottom - 60), fonts)


def draw_compass(draw: ImageDraw.ImageDraw, centre: tuple[float, float], fonts: Fonts) -> None:
    """Стрелка на север."""
    x, y = centre
    draw.polygon(((x, y - 52), (x - 20, y + 20), (x, y + 4), (x + 20, y + 20)), fill=INK)
    draw.text((x - 12, y + 26), "С", font=fonts.label, fill=INK)


def draw_scale_bar(draw: ImageDraw.ImageDraw, corner: tuple[float, float], fonts: Fonts) -> None:
    """Масштабная линейка на пять километров."""
    x, y = corner
    length = 210
    draw.rectangle((x, y, x + length, y + 12), fill=INK)
    draw.rectangle((x + length / 2, y, x + length, y + 12), fill=(255, 255, 255))
    draw.rectangle((x, y, x + length, y + 12), outline=INK, width=3)
    draw.text((x, y - 34), "0", font=fonts.tiny, fill=INK)
    draw.text((x + length - 26, y - 34), "5 км", font=fonts.tiny, fill=INK)


def draw_facts(draw: ImageDraw.ImageDraw, fonts: Fonts) -> None:
    """Панель с цифрами трассы."""
    box = (1610, 250, 2340, 1090)
    left, top, right, _ = box
    draw.rounded_rectangle(box, radius=18, fill=PANEL)

    facts = (
        ("25,0 км", "Дистанция · Қашықтық"),
        ("55 м", "Набор высоты · Биіктік жиыны"),
        ("47 м", "Перепад · Биіктік айырмасы"),
        ("505–552 м", "Высота над морем · Теңіз деңгейінен"),
        ("Туда и обратно", "Разворот на 12,5 км"),
    )
    y = top + 56
    for value, caption in facts:
        draw.text((left + 44, y), value, font=fonts.number, fill=GIANT_BLUE)
        draw.text((left + 46, y + 78), caption, font=fonts.small, fill=MUTED)
        y += 158
        if y < box[3] - 60:
            draw.line((left + 44, y - 34, right - 44, y - 34), fill=(214, 217, 224), width=2)


def draw_profile(draw: ImageDraw.ImageDraw, fonts: Fonts) -> None:
    """Профиль высот во всю ширину под схемой."""
    box = (60, 1120, 2340, 1340)
    left, top, right, bottom = box
    draw.rounded_rectangle(box, radius=18, fill=PANEL)

    plot_left, plot_right = left + 120, right - 40
    plot_top, plot_bottom = top + 46, bottom - 52
    lowest, highest = 500.0, 560.0

    def point(kilometre: float) -> tuple[float, float]:
        x = plot_left + (kilometre / DISTANCE_KM) * (plot_right - plot_left)
        share = (elevation_at(kilometre) - lowest) / (highest - lowest)
        return x, plot_bottom - share * (plot_bottom - plot_top)

    for height in (510, 530, 550):
        y = plot_bottom - (height - lowest) / (highest - lowest) * (plot_bottom - plot_top)
        draw.line((plot_left, y, plot_right, y), fill=(214, 217, 224), width=2)
        draw.text((left + 30, y - 16), f"{height} м", font=fonts.tiny, fill=MUTED)

    outline = [point(step / 4) for step in range(int(DISTANCE_KM * 4) + 1)]
    draw.polygon(
        [(plot_left, plot_bottom), *outline, (plot_right, plot_bottom)],
        fill=(210, 214, 236),
    )
    draw.line(outline, fill=GIANT_BLUE, width=6, joint="curve")

    turn_x, _ = point(TURN_KM)
    draw.line((turn_x, plot_top, turn_x, plot_bottom), fill=ORANGE, width=3)
    draw.text((turn_x + 12, plot_top - 4), "разворот", font=fonts.tiny, fill=ORANGE)

    for kilometre in range(0, int(DISTANCE_KM) + 1, 5):
        x = plot_left + (kilometre / DISTANCE_KM) * (plot_right - plot_left)
        label = f"{kilometre} км" if kilometre == 0 else str(kilometre)
        draw.text((x - 14, plot_bottom + 12), label, font=fonts.tiny, fill=MUTED)


def render(path: Path) -> Path:
    """Нарисовать карту трассы и сохранить в `path`."""
    canvas = Image.new("RGB", (WIDTH, HEIGHT), PAPER)
    draw = ImageDraw.Draw(canvas)
    fonts = Fonts()

    draw_header(draw, canvas, fonts)
    draw_map_panel(draw, fonts)
    draw_facts(draw, fonts)
    draw_profile(draw, fonts)

    path.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(path, "PNG")
    return path
