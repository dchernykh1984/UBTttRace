"""Брендированные инструменты гонки — обёртка над `instruments.scad`.

Файлы называются `medal-*`, как и медали: для участника это одна и та же
награда, просто разной формы.

Измеритель растяжения цепи мы рисуем сами: его геометрию задаёт цепь,
а не автор модели. Скребок кассеты взят готовым — он лежит в
`assets/models/vendor/` вместе с источником и лицензией, наше на нём
только гравировка.
"""

from __future__ import annotations

from pathlib import Path

from .trophies import RenderTask, render

MODEL_PATH = Path(__file__).parent / "assets" / "models" / "instruments.scad"
VENDOR_DIR = MODEL_PATH.parent / "vendor"

KINDS: tuple[tuple[str, str], ...] = (
    ("chain-wear", "Измеритель растяжения цепи, наша модель"),
    ("cassette", "Скребок для чистки кассеты (модель под CC BY 4.0)"),
)


def render_plan() -> tuple[RenderTask, ...]:
    """Что резать в STL: по файлу на инструмент."""
    return tuple(
        RenderTask(filename=f"medal-{kind}.stl", part=kind, definitions={}, comment=comment)
        for kind, comment in KINDS
    )


def render_all(directory: Path, executable: str | None = None) -> list[Path]:
    """Нанести гравировку на все инструменты."""
    return [
        render(directory / task.filename, task, model=MODEL_PATH, executable=executable)
        for task in render_plan()
    ]
