"""Медали участникам — обёртка над параметрической моделью OpenSCAD.

Медаль у всех одна снаружи — диск 50 мм с гравировкой гонки, — но обратная
сторона несёт инструмент, которым велосипедист реально пользуется:

* `spacer` — транспортные проставки под тормозные колодки, одна кромка под
  Shimano, противоположная под SRAM;
* `key` — ключ для пластиковой крышки натяга Shimano Hollowtech II;
* `whistle` — свисток, чтобы отогнать собаку.

Здесь только план нарезки: геометрия живёт в `assets/models/medal.scad`,
а запуск openscad общий с кубками — см. `trophies.py`.
"""

from __future__ import annotations

from pathlib import Path

from .trophies import RenderTask, render

MODEL_PATH = Path(__file__).parent / "assets" / "models" / "medal.scad"

KINDS: tuple[tuple[str, str], ...] = (
    ("spacer", "Проставки под колодки: Shimano 1.8 мм и SRAM 2.8 мм"),
    ("key", "Ключ крышки натяга Shimano Hollowtech II"),
    ("whistle", "Свисток"),
)


def render_plan() -> tuple[RenderTask, ...]:
    """Что именно резать в STL: по файлу на каждое исполнение медали."""
    return tuple(
        RenderTask(
            filename=f"medal-{kind}.stl",
            part=kind,
            definitions={},
            comment=comment,
        )
        for kind, comment in KINDS
    )


def render_all(directory: Path, executable: str | None = None) -> list[Path]:
    """Нарезать все медали."""
    return [
        render(directory / task.filename, task, model=MODEL_PATH, executable=executable)
        for task in render_plan()
    ]
