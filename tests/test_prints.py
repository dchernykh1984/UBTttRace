"""Проверки моделей, нарисованных в Blender.

Эти формы не собираются кодом, поэтому проверять в них нечего, кроме одного:
что в релиз уедет ровно то, что задумано, и ничего лишнего. Цена ошибки
заметная — файлы тяжёлые, а забытая деталь обнаруживается уже у станка.
"""

from __future__ import annotations

import filecmp
from pathlib import Path

from ubt_race_docs.prints import BOTTLE, CASES, MODELS, copy_all, prints_dir, repository_root


def test_prints_live_next_to_the_repository() -> None:
    assert (repository_root() / "3d_print").is_dir()
    assert prints_dir().is_dir()


def test_every_model_is_in_place() -> None:
    for model in MODELS:
        assert model.path.is_file(), f"нет модели {model.source}"


def test_the_bottle_ships_as_five_parts() -> None:
    # Фляжка печатается пятью деталями: две половины корпуса, донышко,
    # крышка и сетка-вкладыш. Недостающая деталь — это несобираемая фляжка.
    assert len(BOTTLE) == 5
    assert len([model for model in BOTTLE if "half" in model.filename]) == 2


def test_every_computer_gets_its_case() -> None:
    assert len(CASES) == 4
    covered = " ".join(model.filename for model in CASES)
    for computer in ("530-830", "540", "1030", "1040"):
        assert computer in covered, f"нет чехла для Edge {computer}"


def test_release_names_are_tidy_and_unique() -> None:
    names = [model.filename for model in MODELS]
    assert len(names) == len(set(names))
    for name in names:
        assert name == name.lower()
        assert " " not in name, "имя уходит в ассет релиза, пробелам там не место"
        assert name.endswith(".stl")


def test_only_stl_goes_to_the_release() -> None:
    # `.blend` лежит в репозитории как исходник для правок, но в релиз
    # не уходит: в слайсер его не понесёшь, а весит он вчетверо больше.
    for model in MODELS:
        assert model.source.endswith(".stl")
        assert ".blend" not in model.filename


def test_blender_sources_stay_in_the_repository() -> None:
    # Обратная сторона предыдущей проверки: .blend не уходит в релиз,
    # но и потеряться не должен — без него модель больше не поправить.
    # У каждого чехла рядом с STL лежит свой рабочий файл.
    for model in CASES:
        blend = model.path.with_suffix(".blend")
        assert blend.is_file(), f"нет рабочего файла {blend.name}"
    blends = {path.name for path in prints_dir().rglob("*.blend")}
    assert "bottles_modified10.blend" in blends
    # Плюс обмеры приборов, по которым чехлы и рисовались.
    references = {name for name in blends if "reference" in name}
    assert len(references) == 4, f"обмеров приборов должно быть четыре, а их {len(references)}"


def test_every_stl_on_disk_is_registered() -> None:
    # Положили новую модель и забыли дописать в MODELS — она молча
    # не попадёт ни в сборку, ни в релиз. Тест ловит это сразу.
    on_disk = {
        str(path.relative_to(prints_dir()))
        for path in prints_dir().rglob("*")
        if path.suffix == ".stl"
    }
    registered = {model.source for model in MODELS}
    forgotten = on_disk - registered
    assert not forgotten, f"модели есть, а записи в MODELS нет: {sorted(forgotten)}"
    missing = registered - on_disk
    assert not missing, f"в MODELS есть модели без файла: {sorted(missing)}"


def test_copy_keeps_the_models_byte_for_byte(tmp_path: Path) -> None:
    # Модель уходит копией, а не пересохранением: прогон чужой сетки через
    # свой экспорт сшил бы вершины и переписал координаты, и получился бы
    # немного другой файл, выданный за тот же самый.
    produced = copy_all(tmp_path)
    assert {path.name for path in produced} == {model.filename for model in MODELS}
    for model in MODELS:
        assert filecmp.cmp(model.path, tmp_path / model.filename, shallow=False)
