"""Командная строка: собирает всё, что нужно распечатать и напечатать.

ubt-race-docs all --out dist
ubt-race-docs bibs --first 1 --last 300
ubt-race-docs trophies --out dist
"""

from __future__ import annotations

import argparse
import subprocess
from collections.abc import Sequence
from pathlib import Path

from . import __version__
from .bibs import FIRST_BIB, LAST_BIB, build_bibs
from .certificates import SPARE_CERTIFICATES, build_certificates
from .trophies import render_all
from .waivers import FORMS, build_waiver
from .workbook import DEFAULT_ROWS, build_workbook

DEFAULT_OUTPUT = Path("dist")


def bibs_name(first: int, last: int) -> str:
    return f"bib-numbers-{first}-{last}.pdf"


def build_documents(
    output: Path,
    first_bib: int = FIRST_BIB,
    last_bib: int = LAST_BIB,
    spare: int = SPARE_CERTIFICATES,
    rows: int = DEFAULT_ROWS,
    background: Path | None = None,
) -> list[Path]:
    """Собрать все печатные документы гонки."""
    produced = [
        build_bibs(output / bibs_name(first_bib, last_bib), first=first_bib, last=last_bib),
        build_certificates(output / "certificates.pdf", spare=spare, background=background),
    ]
    produced += [build_waiver(output / f"waiver-{form.slug}.pdf", form) for form in FORMS]
    produced.append(build_workbook(output / "prize-money.xlsx", rows=rows))
    return produced


def _report(paths: Sequence[Path]) -> None:
    for path in paths:
        print(f"{path} ({path.stat().st_size // 1024} КБ)")


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ubt-race-docs",
        description="Генератор печатных документов гонки UBT TT",
    )
    parser.add_argument("--version", action="version", version=__version__)
    commands = parser.add_subparsers(dest="command", required=True)

    def with_output(subparser: argparse.ArgumentParser) -> argparse.ArgumentParser:
        subparser.add_argument(
            "--out",
            type=Path,
            default=DEFAULT_OUTPUT,
            metavar="DIR",
            help=f"куда складывать результат (по умолчанию {DEFAULT_OUTPUT})",
        )
        return subparser

    bibs = with_output(commands.add_parser("bibs", help="стартовые номера"))
    bibs.add_argument("--first", type=int, default=FIRST_BIB, help="первый номер")
    bibs.add_argument("--last", type=int, default=LAST_BIB, help="последний номер")

    certificates = with_output(commands.add_parser("certificates", help="грамоты"))
    certificates.add_argument(
        "--spare",
        type=int,
        default=SPARE_CERTIFICATES,
        help="сколько добавить незаполненных бланков",
    )
    certificates.add_argument(
        "--background",
        type=Path,
        metavar="FILE",
        help="картинка на весь лист вместо нарисованного фона",
    )

    with_output(commands.add_parser("waivers", help="расписки об ответственности"))

    workbook = with_output(commands.add_parser("workbook", help="таблица призовых"))
    workbook.add_argument(
        "--rows",
        type=int,
        default=DEFAULT_ROWS,
        help="сколько строк протокола подготовить",
    )

    with_output(commands.add_parser("trophies", help="STL кубков (нужен openscad)"))

    everything = with_output(commands.add_parser("all", help="все документы сразу"))
    everything.add_argument("--first", type=int, default=FIRST_BIB, help="первый номер")
    everything.add_argument("--last", type=int, default=LAST_BIB, help="последний номер")
    everything.add_argument("--spare", type=int, default=SPARE_CERTIFICATES)
    everything.add_argument("--rows", type=int, default=DEFAULT_ROWS)
    everything.add_argument(
        "--background",
        type=Path,
        metavar="FILE",
        help="картинка на весь лист вместо нарисованного фона грамот",
    )
    everything.add_argument(
        "--with-trophies",
        action="store_true",
        help="заодно нарезать STL кубков (нужен openscad)",
    )

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Точка входа консольной команды."""
    arguments = _parser().parse_args(argv)
    output: Path = arguments.out
    output.mkdir(parents=True, exist_ok=True)

    try:
        if arguments.command == "bibs":
            produced = [
                build_bibs(
                    output / bibs_name(arguments.first, arguments.last),
                    first=arguments.first,
                    last=arguments.last,
                )
            ]
        elif arguments.command == "certificates":
            produced = [
                build_certificates(
                    output / "certificates.pdf",
                    spare=arguments.spare,
                    background=arguments.background,
                )
            ]
        elif arguments.command == "waivers":
            produced = [build_waiver(output / f"waiver-{form.slug}.pdf", form) for form in FORMS]
        elif arguments.command == "workbook":
            produced = [build_workbook(output / "prize-money.xlsx", rows=arguments.rows)]
        elif arguments.command == "trophies":
            produced = render_all(output)
        else:
            produced = build_documents(
                output,
                first_bib=arguments.first,
                last_bib=arguments.last,
                spare=arguments.spare,
                rows=arguments.rows,
                background=arguments.background,
            )
            if arguments.with_trophies:
                produced += render_all(output)
    except ValueError as error:
        print(f"Ошибка: {error}")
        return 2
    except RuntimeError as error:
        print(f"Ошибка: {error}")
        return 3
    except subprocess.CalledProcessError as error:
        print(f"openscad не смог нарезать модель: {error.stderr.decode('utf-8', 'replace')}")
        return 4
    except subprocess.SubprocessError as error:
        # Сюда попадает в том числе TimeoutExpired: модель считается долго,
        # и на слабой машине лимит вполне достижим.
        print(f"openscad не отработал: {error}")
        return 4

    _report(produced)
    return 0


if __name__ == "__main__":  # pragma: no cover - запуск через `python -m`
    raise SystemExit(main())
