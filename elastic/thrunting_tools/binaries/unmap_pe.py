#!/usr/bin/env python3
"""CLI utility for unmapping PE memory regions"""
# Licensed to Elasticsearch B.V. under one or more contributor
# license agreements. See the NOTICE file distributed with
# this work for additional information regarding copyright
# ownership. Elasticsearch B.V. licenses this file to you under
# the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# 	http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.
import logging
from hashlib import sha256
from pathlib import Path
from typing import BinaryIO, Optional

import pefile
import typer

from elastic.thrunting_tools.common.utils import stream, version_callback

logger = logging.getLogger(__name__)
MAX_CHUNK_SIZE: int = 4096

app = typer.Typer(add_completion=False)


@app.command()
def unmap_pefile(
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
    """
    Process a PE file object, removing the memory mapping. This is useful when analyzing PE objects
    captured from memory. Defaults to reading from standard in and writing to standard out.
    """

    f_in: BinaryIO
    f_out: BinaryIO
    shasum = sha256()

    with stream(path_in, "rb") as f_in, stream(path_out, "wb") as f_out:
        buff = bytearray()
        while True:  # loop until EOF
            _chunk: bytes = f_in.read(MAX_CHUNK_SIZE)
            if not _chunk:  # An empty string is the end
                break
            buff.extend(_chunk)
            shasum.update(_chunk)

        pe: pefile.PE
        try:
            pe = pefile.PE(data=buff)
        except pefile.PEFormatError:
            logger.error("Unable to process file as PE. sha256: %s", shasum.hexdigest())
            raise typer.Exit(1)  # pylint: disable=raise-missing-from

        header_len: int = pe.OPTIONAL_HEADER.SizeOfHeaders
        f_out.write(buff[:header_len])

        entry: pefile.SectionStructure
        for entry in pe.sections:
            f_out.write(
                buff[entry.VirtualAddress : entry.VirtualAddress + entry.SizeOfRawData]
            )


if __name__ == "__main__":
    app()
