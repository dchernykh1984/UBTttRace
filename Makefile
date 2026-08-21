UV   ?= uv
DIST ?= dist

.PHONY: help install lint format typecheck test \
        build kit bibs certificates waivers workbook models clean

help:
	@echo "Разработка:"
	@echo "  make install        поставить зависимости (uv) и хуки pre-commit"
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

install:
	$(UV) sync
	$(UV) run pre-commit install

lint:
	$(UV) run ruff check .
	$(UV) run ruff format --check .

format:
	$(UV) run ruff format .
	$(UV) run ruff check --fix .

typecheck:
	$(UV) run mypy

test:
	$(UV) run pytest

build:
	$(UV) run ubt-race-docs all --out $(DIST)

kit:
	$(UV) run ubt-race-docs all --with-trophies --out $(DIST)

bibs:
	$(UV) run ubt-race-docs bibs --out $(DIST)

certificates:
	$(UV) run ubt-race-docs certificates --out $(DIST)

waivers:
	$(UV) run ubt-race-docs waivers --out $(DIST)

workbook:
	$(UV) run ubt-race-docs workbook --out $(DIST)

models:
	$(UV) run ubt-race-docs trophies --out $(DIST)

clean:
	rm -rf $(DIST) .pytest_cache .ruff_cache .mypy_cache
	find . -name __pycache__ -type d -prune -exec rm -rf {} +
