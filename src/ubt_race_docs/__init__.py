"""Генераторы печатных документов гонки UBT TT."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("ubt-race-docs")
except PackageNotFoundError:  # pragma: no cover - пакет не установлен, работаем из исходников
    __version__ = "0.0.0.dev0"

__all__ = ["__version__"]
