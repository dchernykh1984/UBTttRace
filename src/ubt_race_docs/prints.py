"""Готовые модели для печати: фляжка-хранилище и чехлы велокомпьютеров.

В отличие от кубков и медалей эти формы нарисованы в Blender, а не кодом,
поэтому в репозитории лежат сами файлы: пересобрать их не из чего, они
и есть исходник. Лежат в `3d_print/`, рядом со своими `.blend`.

В релиз уходят **только STL**. `.blend` — это рабочий файл для правок,
нести его в слайсер незачем, а весит он вчетверо больше.

Здесь только опись и копирование: ничего не считается и не пересохраняется.
Модель уходит в сборку байт в байт — прогон чужой сетки через чужой экспорт
дал бы другой файл, выданный за тот же самый.
"""

from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path

PACKAGE_ROOT = Path(__file__).parent
PRINTS_DIRNAME = "3d_print"


def repository_root() -> Path:
    """Корень репозитория — тот каталог, в котором лежит `3d_print`.

    Ищем снизу вверх, а не отсчитываем шаги от пакета: при установке колесом
    пакет лежит в `site-packages`, и фиксированное число шагов промахнулось бы
    мимо моделей.
    """
    for candidate in (PACKAGE_ROOT, *PACKAGE_ROOT.parents):
        if (candidate / PRINTS_DIRNAME).is_dir():
            return candidate
    here = Path.cwd()
    for candidate in (here, *here.parents):
        if (candidate / PRINTS_DIRNAME).is_dir():
            return candidate
    raise RuntimeError(
        f"не найден каталог {PRINTS_DIRNAME} — запускайте из репозитория "
        "или поставьте пакет в режиме разработки (uv sync)"
    )


def prints_dir() -> Path:
    return repository_root() / PRINTS_DIRNAME


@dataclass(frozen=True, slots=True)
class PrintModel:
    """Одна деталь: как файл называется у автора и как уходит в релиз."""

    source: str
    filename: str
    comment: str

    @property
    def path(self) -> Path:
        return prints_dir() / self.source


BOTTLE: tuple[PrintModel, ...] = (
    PrintModel(
        "bottles/B_bottle74_body_half1_cutdown.stl",
        "bottle-body-half1.stl",
        "Половина корпуса фляжки — печатать 1 шт.",
    ),
    PrintModel(
        "bottles/B_bottle74_body_half2_cutdown.stl",
        "bottle-body-half2.stl",
        "Вторая половина корпуса — печатать 1 шт.",
    ),
    PrintModel(
        "bottles/B_bottle74_bottom_cap.stl",
        "bottle-bottom-cap.stl",
        "Донышко фляжки",
    ),
    PrintModel(
        "bottles/B_bottle74_top_lid_text.stl",
        "bottle-top-lid.stl",
        "Верхняя крышка с надписью",
    ),
    PrintModel(
        "bottles/B_bottle74_net_TPU_print2.stl",
        "bottle-net.stl",
        "Сетка-вкладыш, печатать гибким пластиком",
    ),
)

CASES: tuple[PrintModel, ...] = (
    PrintModel(
        "garmin/garmin-530-830-case-v5.stl",
        "case-garmin-530-830.stl",
        "Чехол Garmin Edge 530 и 830",
    ),
    PrintModel(
        "garmin/garmin-540-case-v5.stl",
        "case-garmin-540.stl",
        "Чехол Garmin Edge 540",
    ),
    PrintModel(
        "garmin/garmin-1030-case-v5.stl",
        "case-garmin-1030.stl",
        "Чехол Garmin Edge 1030",
    ),
    PrintModel(
        "garmin/garmin-1040-case-v5.stl",
        "case-garmin-1040.stl",
        "Чехол Garmin Edge 1040",
    ),
)

MODELS: tuple[PrintModel, ...] = BOTTLE + CASES


def copy_all(directory: Path) -> list[Path]:
    """Разложить модели по каталогу сборки под их релизными именами."""
    directory.mkdir(parents=True, exist_ok=True)
    produced = []
    for model in MODELS:
        target = directory / model.filename
        shutil.copyfile(model.path, target)
        produced.append(target)
    return produced
