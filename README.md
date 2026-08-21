# UBT TT — печатные документы гонки

Код, который генерирует всё, что нужно распечатать и напечатать к гонке
**«Открытая контрольная шоссейная тренировка с раздельным стартом UBT»**
(4 октября 2026, Алматинская область, село Кырбалтабай).

Страница гонки: <https://universalbicycle.team/calendar/533/>

В репозитории лежит **только код**. Готовые PDF, XLSX и STL не коммитятся —
их собирает CI и прикладывает к [релизу](../../releases).

## Что получается

| Файл | Что это |
|---|---|
| `bib-numbers-1-300.pdf` | стартовые номера 1–300 на подседельный штырь, по два на лист A4 |
| `certificates.pdf` | грамоты: три места у мужчин и у женщин плюс два пустых бланка |
| `waiver-adult.pdf` | расписка об ответственности совершеннолетнего участника |
| `waiver-minor.pdf` | расписка законного представителя за несовершеннолетнего |
| `prize-money.xlsx` | таблица призовых: вставляешь протокол — считает выплаты |
| `trophy-*.stl` | кубки победителям для 3D-принтера |

Документы двуязычные, русский и казахский. Как это печатать и собирать —
[docs/print.md](docs/print.md).

## Требования

- [uv](https://docs.astral.sh/uv/) — он же поставит нужный Python (3.11+)
- [OpenSCAD](https://openscad.org/) — только для сборки STL-моделей кубков

## Собрать всё локально

Один раз ставим зависимости:

```bash
make install
```

Дальше собираем что нужно — результат всегда складывается в папку `dist/`
внутри проекта (она в `.gitignore`, в репозиторий ничего не попадает):

```bash
make build     # все документы сразу: номера, грамоты, расписки, таблица призовых
make kit       # то же самое плюс STL кубков (нужен openscad)
```

По одному документу:

| Команда | Что появится в `dist/` |
|---|---|
| `make bibs` | `bib-numbers-1-300.pdf` |
| `make certificates` | `certificates.pdf` |
| `make waivers` | `waiver-adult.pdf`, `waiver-minor.pdf` |
| `make workbook` | `prize-money.xlsx` |
| `make models` | `trophy-*.stl` (нужен openscad) |

`make clean` удаляет `dist/` и кэши.

Если нужны нестандартные параметры — та же программа доступна напрямую,
`--help` покажет всё:

```bash
uv run ubt-race-docs bibs --first 1 --last 500 --out dist
uv run ubt-race-docs certificates --spare 5 --out dist
uv run ubt-race-docs certificates --background ~/Pictures/фон.png --out dist
uv run ubt-race-docs --help
```

Фон грамоты меняется и без ключа: положите картинку A4 в
[assets/backgrounds/](src/ubt_race_docs/assets/backgrounds/) — она подхватится сама.

## Разработка

Зависимости живут в `pyproject.toml`, версии зафиксированы в `uv.lock` —
у всех и в CI ставится ровно одно и то же.

```bash
make lint        # ruff check + ruff format --check
make typecheck   # mypy
make test        # pytest
```

`make install` заодно ставит хуки [pre-commit](https://pre-commit.com/): перед
каждым коммитом прогоняются ruff, mypy и мелкая гигиена файлов. Разово по всему
репозиторию — `uv run pre-commit run --all-files`.

## Структура

```
src/ubt_race_docs/
    race.py            паспорт гонки: название, дата, место, денежные правила
    bibs.py            стартовые номера
    certificates.py    грамоты
    waivers.py         расписки об ответственности
    prizes.py          распределение призового фонда по положению
    workbook.py        книга Excel с живыми формулами
    trophies.py        запуск openscad для кубков
    cli.py             командная строка
    background.py      фон печатного листа
    brand.py           цвета команды и логотип
    assets/fonts/      DejaVu — кириллица и казахские буквы
    assets/images/     логотип UBT
    assets/backgrounds/ сюда кладётся своя картинка под грамоту
    assets/models/     trophy.scad — параметрическая модель кубка
tests/                 тесты
docs/                  инструкции по печати и сборке
```

Данные гонки заданы один раз в [race.py](src/ubt_race_docs/race.py) — название,
дата, место, категории и денежные правила. Меняются там, а не в каждом документе.

## Версии и релизы

Ветка `main` защищена процессом [release-please](https://github.com/googleapis/release-please):

1. Заголовки коммитов — [Conventional Commits](https://www.conventionalcommits.org/ru/v1.0.0/).
   `feat:` поднимает minor-версию, `fix:` — patch, `feat!:`/`BREAKING CHANGE` — major.
2. После мерджа в `main` release-please открывает (или обновляет) Release PR
   с версией и `CHANGELOG.md`.
3. Мердж Release PR создаёт тег и GitHub Release, а CI собирает и прикладывает
   к нему готовые файлы для печати.

Версия проекта лежит ровно в одном месте — `__version__`
в [src/ubt_race_docs/\_\_init\_\_.py](src/ubt_race_docs/__init__.py); `pyproject.toml`
берёт её оттуда (`dynamic = ["version"]`), а release-please правит эту строку
по пометке `x-release-please-version`. Так релизный PR не задевает `uv.lock`,
и `uv sync --locked` в CI не ломается на поднятой версии.

> Чтобы release-please мог открывать PR, в настройках репозитория должно быть
> включено **Settings → Actions → General → Workflow permissions →
> Allow GitHub Actions to create and approve pull requests**.
