PYTHON ?= python3
VENV   ?= .venv
BIN     = $(VENV)/bin
DIST   ?= dist

.PHONY: help venv install lint format typecheck test build models clean

help:
	@echo "make install   - создать venv и поставить зависимости"
	@echo "make lint      - ruff check + ruff format --check"
	@echo "make format    - отформатировать код"
	@echo "make typecheck - mypy"
	@echo "make test      - pytest"
	@echo "make build     - собрать PDF/XLSX в $(DIST)"
	@echo "make models    - собрать STL кубков в $(DIST) (нужен openscad)"
	@echo "make clean     - удалить $(DIST) и кэши"

$(VENV):
	$(PYTHON) -m venv $(VENV)

install: $(VENV)
	$(BIN)/pip install --upgrade pip
	$(BIN)/pip install -e ".[dev]"

lint:
	$(BIN)/ruff check .
	$(BIN)/ruff format --check .

format:
	$(BIN)/ruff format .
	$(BIN)/ruff check --fix .

typecheck:
	$(BIN)/mypy

test:
	$(BIN)/pytest

build:
	$(BIN)/ubt-race-docs all --out $(DIST)

models:
	$(BIN)/ubt-race-docs trophies --out $(DIST)

clean:
	rm -rf $(DIST) .pytest_cache .ruff_cache .mypy_cache
	find . -name __pycache__ -type d -prune -exec rm -rf {} +
