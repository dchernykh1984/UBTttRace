"""Позволяет запускать пакет как `python -m ubt_race_docs`."""

from .cli import main

if __name__ == "__main__":
    raise SystemExit(main())
