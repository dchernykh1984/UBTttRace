# UBT TT — печатные документы гонки

Код, который генерирует всё, что нужно распечатать и напечатать к гонке
**«Открытая контрольная шоссейная тренировка с раздельным стартом UBT»**
(4 октября 2026, Алматинская область, село Кырбалтабай).

Страница гонки: <https://universalbicycle.team/calendar/533/>

В репозитории лежит **только код**. Готовые PDF, XLSX и STL не коммитятся —
их собирает CI и прикладывает к [релизу](../../releases).

## Требования

- Python 3.11+
- [OpenSCAD](https://openscad.org/) — только для сборки STL-моделей кубков

## Быстрый старт

```bash
make install     # venv + зависимости
make lint        # ruff check + ruff format --check
make typecheck   # mypy
make test        # pytest
make build       # PDF и XLSX в dist/
make models      # STL кубков в dist/ (нужен openscad)
```

## Структура

```
src/ubt_race_docs/   генераторы документов (Python)
models/              параметрические 3D-модели кубков (OpenSCAD)
scripts/             сборка моделей
tests/               тесты
docs/                инструкции по печати и сборке
```

## Версии и релизы

Ветка `main` защищена процессом [release-please](https://github.com/googleapis/release-please):

1. Заголовки коммитов — [Conventional Commits](https://www.conventionalcommits.org/ru/v1.0.0/).
   `feat:` поднимает minor-версию, `fix:` — patch, `feat!:`/`BREAKING CHANGE` — major.
2. После мерджа в `main` release-please открывает (или обновляет) Release PR
   с версией и `CHANGELOG.md`.
3. Мердж Release PR создаёт тег и GitHub Release, а CI собирает и прикладывает
   к нему готовые файлы для печати.

> Чтобы release-please мог открывать PR, в настройках репозитория должно быть
> включено **Settings → Actions → General → Workflow permissions →
> Allow GitHub Actions to create and approve pull requests**.
