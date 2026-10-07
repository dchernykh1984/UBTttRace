#!/usr/bin/env python3
"""Отформатировать python-файлы, изменённые за ход.

pre-commit сделает то же самое на коммите, но тогда он валит первую попытку
и её приходится повторять. Отформатировать заранее дешевле.

Здесь это хук `Stop`, а не `PostToolUse`, как в Claude Code: в Codex
PostToolUse срабатывает только на команды оболочки, и правки файлов мимо
него проходят. Поэтому файл берётся не из полезной нагрузки хука, а из
того, что git видит изменённым в рабочем дереве.
"""

from __future__ import annotations

import pathlib
import subprocess
import sys


def changed_python_files(root: pathlib.Path) -> list[pathlib.Path]:
    """Изменённые и новые .py в рабочем дереве."""
    names: set[str] = set()
    for command in (
        ["git", "diff", "--name-only", "-z", "HEAD"],
        ["git", "ls-files", "--others", "--exclude-standard", "-z"],
    ):
        answer = subprocess.run(command, capture_output=True, text=True, cwd=root, check=False)
        if answer.returncode == 0:
            names.update(name for name in answer.stdout.split("\0") if name)
    return [
        root / name for name in sorted(names) if name.endswith(".py") and (root / name).is_file()
    ]


def main() -> int:
    root = pathlib.Path.cwd().resolve()
    files = changed_python_files(root)
    if not files:
        return 0

    ruff = root / ".venv" / "bin" / "ruff"
    subprocess.run(
        [str(ruff) if ruff.exists() else "ruff", "format", "--quiet", *map(str, files)],
        check=False,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
