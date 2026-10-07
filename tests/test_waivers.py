"""Проверки расписок об ответственности."""

import re
from pathlib import Path

import pytest
from pypdf import PdfReader

from ubt_race_docs.race import RACE
from ubt_race_docs.waivers import (
    ADULT_FORM,
    FORMS,
    MINOR_FORM,
    WaiverForm,
    WaiverLayout,
    build_waiver,
)


def render(tmp_path: Path, form: WaiverForm) -> str:
    output = build_waiver(tmp_path / f"{form.slug}.pdf", form)
    reader = PdfReader(output)
    # Два разворота — это лист, напечатанный с двух сторон; на регистрации
    # участник по-прежнему получает один лист. Третья страница означала бы,
    # что бланк разросся и его пора сокращать.
    assert len(reader.pages) <= 2, "расписка должна умещаться на лист с оборотом"
    # Переносы строк в PDF рвут фразы посередине, поэтому склеиваем пробелы:
    # иначе проверка «есть ли такая формулировка» зависит от ширины колонки.
    return re.sub(r"\s+", " ", "\n".join(page.extract_text() for page in reader.pages))


def test_forms_are_separate_documents() -> None:
    assert {form.slug for form in FORMS} == {"adult", "minor"}


def test_adult_form_is_signed_by_the_participant(tmp_path: Path) -> None:
    text = render(tmp_path, ADULT_FORM)
    assert "РАСПИСКА ОБ ОТВЕТСТВЕННОСТИ УЧАСТНИКА" in text
    assert "ҚАТЫСУШЫНЫҢ ЖАУАПКЕРШІЛІГІ ТУРАЛЫ ҚОЛХАТ" in text
    assert "законным представителем" not in text


def test_minor_form_collects_both_the_child_and_the_representative(tmp_path: Path) -> None:
    text = render(tmp_path, MINOR_FORM)
    assert "РАСПИСКА ЗАКОННОГО ПРЕДСТАВИТЕЛЯ" in text
    assert "Законный представитель · Заңды өкіл" in text
    assert "Несовершеннолетний участник · Кәмелетке толмаған қатысушы" in text
    assert "Кем приходится · Кім болып келеді" in text


@pytest.mark.parametrize("form", FORMS, ids=[form.slug for form in FORMS])
def test_every_form_states_the_key_risks(tmp_path: Path, form: WaiverForm) -> None:
    text = render(tmp_path, form)
    assert "Правила дорожного движения" in text
    assert "Қазақстан Республикасының" in text
    assert "шлеме" in text or "шлеммен" in text
    assert "персональных данных" in text


@pytest.mark.parametrize("form", FORMS, ids=[form.slug for form in FORMS])
def test_consent_to_personal_data_names_the_operator_and_the_way_out(
    tmp_path: Path, form: WaiverForm
) -> None:
    # Закон РК «О персональных данных и их защите» требует согласия
    # осведомлённого: кто обрабатывает, зачем, куда это уходит и как
    # согласие отозвать. Без любого из четырёх согласие спорное.
    text = render(tmp_path, form)
    assert RACE.organizer in text, "в согласии не назван тот, кто обрабатывает данные"
    assert "протоколы" in text or "протоколов" in text
    assert "социальных сетях" in text, "публикация в соцсетях — это тоже распространение"
    assert "до отзыва" in text and "отозвать" in text


@pytest.mark.parametrize("form", FORMS, ids=[form.slug for form in FORMS])
def test_consent_to_filming_lets_the_organiser_use_the_shots(
    tmp_path: Path, form: WaiverForm
) -> None:
    # Статья 145 ГК РК: чужое изображение без согласия использовать нельзя.
    # Согласие «на съёмку» без права использования ничего не даёт.
    text = render(tmp_path, form)
    assert "фото- и видеосъёмку" in text or "фото- и видеосъёмку ребёнка" in text
    assert "партнёрами" in text
    assert "без ограничения срока и территории" in text
    assert "рекламы" in text


@pytest.mark.parametrize("form", FORMS, ids=[form.slug for form in FORMS])
def test_every_form_says_what_the_organiser_does_not_provide(
    tmp_path: Path, form: WaiverForm
) -> None:
    # Главная защита организатора — не отказ от претензий, а то, что
    # участник заранее знал, чего ему не обещали.
    text = render(tmp_path, form)
    assert "не перекрывают дорогу" in text
    assert "медицинское сопровождение" in text
    assert "не страхуют" in text


@pytest.mark.parametrize("form", FORMS, ids=[form.slug for form in FORMS])
def test_claims_are_waived_only_where_the_law_allows(tmp_path: Path, form: WaiverForm) -> None:
    # Отказ от права на обращение в суд недействителен, и ответственность
    # за вред по своей вине организатор снять с себя не может. Поэтому
    # оговорка про вину обязана стоять рядом с отказом от претензий.
    text = render(tmp_path, form)
    assert "претензий" in text
    assert "по их вине" in text, "безоговорочный отказ от претензий ничтожен"


@pytest.mark.parametrize("form", FORMS, ids=[form.slug for form in FORMS])
def test_damage_to_others_stays_with_the_participant(tmp_path: Path, form: WaiverForm) -> None:
    # Гонка идёт по открытой дороге: кто платит, если участник собьёт
    # пешехода, должно быть написано до старта, а не выясняться после.
    text = render(tmp_path, form)
    assert "иным лицам или их имуществу" in text


@pytest.mark.parametrize("form", FORMS, ids=[form.slug for form in FORMS])
def test_emergency_contact_is_collected_with_their_consent(
    tmp_path: Path, form: WaiverForm
) -> None:
    # В бланке участник вписывает чужой телефон. Это персональные данные
    # третьего лица, и основание на них нужно отдельное.
    text = render(tmp_path, form)
    assert "с согласия этого человека" in text


def test_adult_form_confirms_the_age(tmp_path: Path) -> None:
    assert "Мне исполнилось 18 лет" in render(tmp_path, ADULT_FORM)


@pytest.mark.parametrize("form", FORMS, ids=[form.slug for form in FORMS])
def test_every_form_has_the_race_and_a_place_to_sign(tmp_path: Path, form: WaiverForm) -> None:
    text = render(tmp_path, form)
    assert "День рождения UBT" in text
    assert "4 октября 2026 года" in text
    assert "Подпись · Қолы" in text
    assert "Дата · Күні" in text
    assert "Стартовый номер · Старттық нөмірі" in text


@pytest.mark.parametrize("form", FORMS, ids=[form.slug for form in FORMS])
def test_statements_are_numbered_the_same_in_both_languages(
    tmp_path: Path, form: WaiverForm
) -> None:
    text = render(tmp_path, form)
    for index in range(1, len(form.statements) + 1):
        assert text.count(f"{index}. ") >= 2


def test_overflowing_layout_is_reported(tmp_path: Path) -> None:
    # Длинный бланк переносится на оборот, а вот пункт, который не влезает
    # на пустую страницу целиком, перенести некуда — об этом надо кричать,
    # а не печатать обрезанное обязательство.
    with pytest.raises(ValueError, match="не помещается на лист"):
        build_waiver(tmp_path / "narrow.pdf", MINOR_FORM, WaiverLayout(statement_leading=400))
