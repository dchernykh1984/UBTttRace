PYTHON ?= python3
VENV   ?= .venv
BIN     = $(VENV)/bin
DIST   ?= dist

.PHONY: help venv install lint format typecheck test \
        build kit bibs certificates waivers workbook models clean

help:
	@echo "Разработка:"
	@echo "  make install        создать venv и поставить зависимости"
	@echo "  make lint           ruff check + ruff format --check"
	@echo "  make typecheck      mypy"
	@echo "  make test           pytest"
	@echo ""
	@echo "Сборка документов в ./$(DIST):"
	@echo "  make build          все документы (PDF и XLSX)"
	@echo "  make kit            все документы и кубки"
	@echo "  make bibs           стартовые номера"
	@echo "  make certificates   грамоты"
	@echo "  make waivers        расписки об ответственности"
	@echo "  make workbook       таблица призовых"
	@echo "  make models         STL кубков (нужен openscad)"
	@echo ""
	@echo "  make clean          удалить ./$(DIST) и кэши"

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

kit:
	$(BIN)/ubt-race-docs all --with-trophies --out $(DIST)

bibs:
	$(BIN)/ubt-race-docs bibs --out $(DIST)

certificates:
	$(BIN)/ubt-race-docs certificates --out $(DIST)

waivers:
	$(BIN)/ubt-race-docs waivers --out $(DIST)

workbook:
	$(BIN)/ubt-race-docs workbook --out $(DIST)

models:
	$(BIN)/ubt-race-docs trophies --out $(DIST)

clean:
	rm -rf $(DIST) .pytest_cache .ruff_cache .mypy_cache
	find . -name __pycache__ -type d -prune -exec rm -rf {} +
