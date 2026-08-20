"""Проверки расписок об ответственности."""

from pathlib import Path

import pytest
from pypdf import PdfReader

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
    assert len(reader.pages) == 1, "расписка должна умещаться на один лист"
    return reader.pages[0].extract_text()


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
def test_every_form_has_the_race_and_a_place_to_sign(tmp_path: Path, form: WaiverForm) -> None:
    text = render(tmp_path, form)
    assert "Открытая контрольная шоссейная тренировка" in text
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
    with pytest.raises(ValueError, match="не помещается на лист"):
        build_waiver(tmp_path / "narrow.pdf", MINOR_FORM, WaiverLayout(margin=70 * 72 / 25.4))
