#!/usr/bin/env python3
import sys
import urllib.parse
from pathlib import Path
from typing import Optional, TextIO

import typer

from elastic.thrunting_tools.common.utils import version_callback

MAX_BLOCK_SIZE: int = 4096

app = typer.Typer(add_completion=False)


def block_generator(stream: TextIO) -> str:
    _block: str = ""
    while True:  # Loop until EOF
        _block = stream.read(MAX_BLOCK_SIZE)
        if not _block:
            break

        yield _block


@app.command()
def url_decode(
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
    version: Optional[bool] = typer.Option(  # pylint: disable=unused-argument
        None, "--version", callback=version_callback, help="Show version info and exit"
    ),
):
    f_in = sys.stdin if str(path_in) == "-" else path_in.open("r")
    f_out = sys.stdout if str(path_out) == "-" else path_out.open("w")
    for block in block_generator(f_in):
        f_out.write(urllib.parse.unquote(block))


if __name__ == "__main__":
    app()
