"""Кубки победителям — обёртка над параметрической моделью OpenSCAD.

Кубок печатается за первое место у мужчин и у женщин. Чаша у них общая,
различаются только подставки — на них выгравированы гонка, место и категория,
поэтому чашу достаточно нарезать один раз.

Здесь только сборка команды и запуск openscad: сама геометрия живёт
в `assets/models/trophy.scad`.
"""

from __future__ import annotations

import os
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

from .race import CATEGORIES, RACE, Category, place_title

MODEL_PATH = Path(__file__).parent / "assets" / "models" / "trophy.scad"
FONT_PATH = Path(__file__).parent / "assets" / "fonts"
OPENSCAD = "openscad"
WINNER_PLACE = 1


@dataclass(frozen=True, slots=True)
class Trophy:
    """Кубок конкретной категории."""

    category: Category
    place: int = WINNER_PLACE

    def definitions(self) -> dict[str, str]:
        """Надписи, которые уходят в модель параметрами `-D`."""
        return {
            "title_line": f"{RACE.short_title} · {RACE.date_numeric}",
            "place_line": place_title(self.place).one_line(),
            "category_line": self.category.name.one_line(),
        }


@dataclass(frozen=True, slots=True)
class RenderTask:
    """Одна нарезка модели в STL."""

    filename: str
    part: str
    definitions: dict[str, str]
    comment: str


def trophies() -> tuple[Trophy, ...]:
    """Кубки, которые нужны на награждении."""
    return tuple(Trophy(category) for category in CATEGORIES)


def render_plan() -> tuple[RenderTask, ...]:
    """Что именно резать в STL."""
    tasks: list[RenderTask] = [
        RenderTask(
            filename="trophy-cup.stl",
            part="cup",
            definitions={},
            comment="Чаша, одна и та же для обоих кубков — печатать 2 шт.",
        )
    ]
    for trophy in trophies():
        code = trophy.category.code
        tasks.append(
            RenderTask(
                filename=f"trophy-base-{code}.stl",
                part="base",
                definitions=trophy.definitions(),
                comment=f"Подставка с гравировкой: {trophy.category.name.one_line()}",
            )
        )
        tasks.append(
            RenderTask(
                filename=f"trophy-assembled-{code}.stl",
                part="all",
                definitions=trophy.definitions(),
                comment="Кубок целиком — если печатать одной деталью",
            )
        )
    return tuple(tasks)


def openscad_command(
    output: Path,
    task: RenderTask,
    model: Path = MODEL_PATH,
    executable: str = OPENSCAD,
) -> list[str]:
    """Командная строка openscad для одной нарезки."""
    command = [executable, "-o", str(output)]
    for name, value in {"part": task.part, **task.definitions}.items():
        command += ["-D", f'{name}="{value}"']
    command.append(str(model))
    return command


def openscad_executable() -> str | None:
    """Путь к openscad или None, если его нет в системе."""
    return shutil.which(os.environ.get("OPENSCAD", OPENSCAD))


def render(
    output: Path,
    task: RenderTask,
    model: Path = MODEL_PATH,
    executable: str | None = None,
    timeout: float = 900,
) -> Path:
    """Нарезать STL. Требует установленного openscad."""
    binary = executable or openscad_executable()
    if binary is None:
        raise RuntimeError(
            "не найден openscad — поставьте его (https://openscad.org/) "
            "или укажите путь в переменной окружения OPENSCAD"
        )

    output.parent.mkdir(parents=True, exist_ok=True)
    environment = dict(os.environ)
    # Чтобы кириллица в гравировке рисовалась вшитым в проект шрифтом,
    # а не тем, что случайно оказался на машине.
    environment["OPENSCAD_FONT_PATH"] = str(FONT_PATH)
    subprocess.run(
        openscad_command(output, task, model, binary),
        check=True,
        capture_output=True,
        timeout=timeout,
        env=environment,
    )
    return output


def render_all(directory: Path, executable: str | None = None) -> list[Path]:
    """Нарезать все STL по плану."""
    return [
        render(directory / task.filename, task, executable=executable) for task in render_plan()
    ]
