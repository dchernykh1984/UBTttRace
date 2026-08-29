"""Проверки командной строки."""

import subprocess
from pathlib import Path

import pytest

from ubt_race_docs import __version__, trophies
from ubt_race_docs.cli import main


def test_all_builds_the_whole_print_kit(tmp_path: Path) -> None:
    assert main(["all", "--out", str(tmp_path), "--last", "4"]) == 0
    produced = sorted(path.name for path in tmp_path.iterdir())
    assert produced == [
        "bib-numbers-1-4.pdf",
        "certificates.pdf",
        "map.png",
        "prize-money.xlsx",
        "waiver-adult.pdf",
        "waiver-minor.pdf",
    ]


def test_each_command_writes_only_its_own_files(tmp_path: Path) -> None:
    assert main(["waivers", "--out", str(tmp_path)]) == 0
    assert sorted(path.name for path in tmp_path.iterdir()) == [
        "waiver-adult.pdf",
        "waiver-minor.pdf",
    ]


def test_bib_range_is_part_of_the_file_name(tmp_path: Path) -> None:
    assert main(["bibs", "--out", str(tmp_path), "--first", "5", "--last", "9"]) == 0
    assert (tmp_path / "bib-numbers-5-9.pdf").is_file()


def test_output_directory_is_created(tmp_path: Path) -> None:
    target = tmp_path / "nested" / "dist"
    assert main(["workbook", "--out", str(target), "--rows", "20"]) == 0
    assert (target / "prize-money.xlsx").is_file()


def test_bad_arguments_are_reported_not_traced(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert main(["bibs", "--out", str(tmp_path), "--first", "10", "--last", "1"]) == 2
    assert "Ошибка" in capsys.readouterr().out


def test_missing_openscad_is_reported(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(trophies, "openscad_executable", lambda: None)
    assert main(["trophies", "--out", str(tmp_path)]) == 3
    assert "openscad" in capsys.readouterr().out


def test_version_is_printed(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exit_info:
        main(["--version"])
    assert exit_info.value.code == 0
    assert capsys.readouterr().out.strip() == __version__


def test_command_is_required(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exit_info:
        main([])
    assert exit_info.value.code == 2


def test_openscad_timeout_is_reported(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    def timeout(*_args: object, **_kwargs: object) -> None:
        raise subprocess.TimeoutExpired(cmd="openscad", timeout=900)

    monkeypatch.setattr(trophies.subprocess, "run", timeout)
    monkeypatch.setattr(trophies, "openscad_executable", lambda: "/usr/bin/openscad")
    assert main(["trophies", "--out", str(tmp_path)]) == 4
    assert "openscad не отработал" in capsys.readouterr().out


def test_openscad_failure_is_reported(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    def failure(*_args: object, **_kwargs: object) -> None:
        raise subprocess.CalledProcessError(1, "openscad", stderr=b"ERROR: Assertion failed")

    monkeypatch.setattr(trophies.subprocess, "run", failure)
    monkeypatch.setattr(trophies, "openscad_executable", lambda: "/usr/bin/openscad")
    assert main(["trophies", "--out", str(tmp_path)]) == 4
    assert "Assertion failed" in capsys.readouterr().out
