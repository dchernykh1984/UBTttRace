"""Проверки обвязки версионирования.

Версия живёт в `__init__.py`, а не в `pyproject.toml`: релизный PR правит её
вместе с манифестом, а `uv.lock` при этом не устаревает и `uv sync --locked`
в CI продолжает работать.
"""

from __future__ import annotations

import json
import tomllib
from pathlib import Path

from ubt_race_docs import __version__

REPO = Path(__file__).resolve().parents[1]
VERSION_FILE = REPO / "src" / "ubt_race_docs" / "__init__.py"


def test_version_matches_the_release_manifest() -> None:
    manifest = json.loads((REPO / ".release-please-manifest.json").read_text(encoding="utf-8"))
    assert __version__ == manifest["."]


def test_lockfile_does_not_pin_the_project_version() -> None:
    lock = tomllib.loads((REPO / "uv.lock").read_text(encoding="utf-8"))
    package = next(item for item in lock["package"] if item["name"] == "ubt-race-docs")
    assert "version" not in package, (
        "в uv.lock снова попала версия проекта — релизный PR сломает `uv sync --locked`"
    )


def test_pyproject_takes_the_version_from_the_package() -> None:
    pyproject = tomllib.loads((REPO / "pyproject.toml").read_text(encoding="utf-8"))
    assert "version" in pyproject["project"]["dynamic"]
    assert "version" not in pyproject["project"]
    assert pyproject["tool"]["setuptools"]["dynamic"]["version"] == {
        "attr": "ubt_race_docs.__version__"
    }


def test_release_please_is_told_to_update_the_version_file() -> None:
    config = json.loads((REPO / "release-please-config.json").read_text(encoding="utf-8"))
    assert "src/ubt_race_docs/__init__.py" in config["packages"]["."]["extra-files"]
    # Без этой пометки release-please не поймёт, какую строку править.
    assert "x-release-please-version" in VERSION_FILE.read_text(encoding="utf-8")
