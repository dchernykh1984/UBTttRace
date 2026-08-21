"""Кубки победителям — обёртка над параметрической моделью OpenSCAD.

Кубок печатается победителю у мужчин и у женщин. Велосипед у них общий,
различаются только подставки — на них выгравированы гонка, категория и то,
кого награждаем, — поэтому велосипед достаточно нарезать один раз.

Здесь только сборка команды и запуск openscad: сама геометрия живёт
в `assets/models/trophy.scad`.
"""

from __future__ import annotations

import os
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

from .race import CATEGORIES, RACE, Category

MODEL_PATH = Path(__file__).parent / "assets" / "models" / "trophy.scad"
FONT_PATH = Path(__file__).parent / "assets" / "fonts"
OPENSCAD = "openscad"


def engraving(category: Category) -> dict[str, str]:
    """Надписи для подставки, которые уходят в модель параметрами `-D`."""
    return {
        "title_line": f"{RACE.short_title} · {RACE.date_numeric}",
        "place_line": category.winner.one_line(),
        "category_line": category.name.one_line(),
    }


@dataclass(frozen=True, slots=True)
class RenderTask:
    """Одна нарезка модели в STL."""

    filename: str
    part: str
    definitions: dict[str, str]
    comment: str


def render_plan() -> tuple[RenderTask, ...]:
    """Что именно резать в STL."""
    tasks: list[RenderTask] = [
        RenderTask(
            filename="trophy-bike.stl",
            part="bike",
            definitions={},
            comment="Велосипед, одинаковый для обоих кубков — печатать 2 шт.",
        )
    ]
    for category in CATEGORIES:
        code = category.code
        tasks.append(
            RenderTask(
                filename=f"trophy-base-{code}.stl",
                part="base",
                definitions=engraving(category),
                comment=f"Подставка с гравировкой: {category.winner.one_line()}",
            )
        )
        tasks.append(
            RenderTask(
                filename=f"trophy-assembled-{code}.stl",
                part="all",
                definitions=engraving(category),
                comment="Кубок в сборе — для предпросмотра, печатать лучше по деталям",
            )
        )
    return tuple(tasks)


def scad_string(value: str) -> str:
    """Строковый литерал OpenSCAD.

    Надписи задаются в `race.py` руками, и кавычка или обратный слеш в них
    превратили бы `-D` в синтаксически битый кусок модели.
    """
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def openscad_command(
    output: Path,
    task: RenderTask,
    model: Path = MODEL_PATH,
    executable: str = OPENSCAD,
) -> list[str]:
    """Командная строка openscad для одной нарезки."""
    command = [executable, "-o", str(output)]
    for name, value in {"part": task.part, **task.definitions}.items():
        command += ["-D", f"{name}={scad_string(value)}"]
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
