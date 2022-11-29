#!/usr/bin/env python3
import sys
import zlib
from pathlib import Path
from typing import BinaryIO, Optional

import typer

from elastic.thrunting_tools.common.utils import stream, version_callback

MAX_CHUNK_SIZE: int = 4096

app = typer.Typer(add_completion=False)


def chunk_generator(stream_in: BinaryIO) -> str:
    _deflator = zlib.compressobj()
    while True:  # Loop until EOF
        _chunk = stream_in.read(MAX_CHUNK_SIZE)
        if not _chunk:
            yield _deflator.flush()
            break
        yield _deflator.compress(_chunk)


@app.command()
def zlib_deflate(
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

    with stream(path_in, "rb") as f_in, stream(path_out, "wb") as f_out:
        gen = chunk_generator(f_in)
        for chunk in gen:
            f_out.write(chunk)


if __name__ == "__main__":
    app()
