#!/usr/bin/env python3
import sys
from pathlib import Path
from typing import Optional, TextIO

import typer

from elastic.thrunting_tools.common.utils import version_callback

MAX_BLOCK_SIZE: int = 4096


app = typer.Typer(add_completion=False)


def chunk_generator(stream: TextIO, delimiter: str) -> str:
    _buffer: str = ""
    while True:  # Loop until EOF
        _chunk = stream.read(MAX_BLOCK_SIZE)
        if not _chunk:
            yield _buffer
            break

        _buffer += _chunk
        while True:
            _part, _, _buffer = _buffer.partition(delimiter)
            if _ != delimiter:  # no more delimiters
                _buffer = _part
                break
            else:
                yield _part


def validate_base(value: int):
    if value < 2 or value > 36:
        raise typer.BadParameter("Base must be 2<=base<=36")
    return value


@app.command()
def from_charcode(
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
    for code in chunk_generator(f_in, delimiter):
        if code.isalnum():
            f_out.write(chr(int(code, base)))


if __name__ == "__main__":
    app()
