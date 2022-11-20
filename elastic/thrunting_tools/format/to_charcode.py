#!/usr/bin/env python3
import string
import sys
from pathlib import Path
from typing import Optional, TextIO

import typer

from elastic.thrunting_tools.common.utils import version_callback

ALPHABET: str = string.digits + string.ascii_letters
MAX_CHUNK_SIZE: int = 4096

app = typer.Typer(add_completion=False)


def int2base(value: int, base: int) -> str:
    _digits: list[str] = []
    while value:
        _digits.append(ALPHABET[value % base])
        value = value // base

    _digits.reverse()

    return "".join(_digits)


def chunk_generator(stream: TextIO) -> str:
    for _chunk in stream:
        if not _chunk:
            break

        for _chr in _chunk:
            yield _chr


def validate_base(value: int):
    if value < 2 or value > 36:
        raise typer.BadParameter("Base must be 2<=base<=36")
    return value


@app.command()
def to_charcode(
    path_in: Path = typer.Option(
        "-",
        "--input",
        "-i",
        allow_dash=True,
        readable=True,
        file_okay=True,
        dir_okay=False,
        help="Filename for input stream",
    ),
    path_out: Path = typer.Option(
        "-",
        "--output",
        "-o",
        allow_dash=True,
        writable=True,
        file_okay=True,
        dir_okay=False,
        help="Filename for output stream",
    ),
    delimiter: Optional[str] = typer.Option(" ", "--delimiter", "-d"),
    base: Optional[int] = typer.Option(16, "--base", "-b", callback=validate_base),
    version: Optional[bool] = typer.Option(  # pylint: disable=unused-argument
        None, "--version", callback=version_callback, help="Show version info and exit"
    ),
):
    f_in = sys.stdin if str(path_in) == "-" else path_in.open("r")
    f_out = sys.stdout if str(path_out) == "-" else path_out.open("w")
    first: bool = True
    for _chr in chunk_generator(f_in):
        if first:
            first = False
        else:
            f_out.write(delimiter)
        f_out.write(int2base(ord(_chr), base))


if __name__ == "__main__":
    app()
