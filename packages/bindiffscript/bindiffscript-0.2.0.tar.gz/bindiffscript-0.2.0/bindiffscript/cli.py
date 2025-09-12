#!/usr/bin/env python3
#
# bindiffscript
# Copyright (C) 2025 - Frans Fürst
#
# bindiffscript is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the
# Free Software Foundation, either version 3 of the License, or (at your option)
# any later version.
#
# bindiffscript is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY
# or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details at
#  <http://www.gnu.org/licenses/>.
#
# Anyway this project is not free for commercial machine learning. If you're
# using any content of this repository to train any sort of machine learned
# model (e.g. LLMs), you agree to make the whole model trained with this
# repository and all data needed to train (i.e. reproduce) the model publicly
# and freely available (i.e. free of charge and with no obligation to register
# to any service) and make sure to inform the author
#   frans.fuerst@protonmail.com via email how to get and use that model and any
# sources needed to train it.

"""Bindiffscript"""

from argparse import ArgumentParser
from argparse import Namespace as Args
from collections.abc import Sequence
from contextlib import suppress
from itertools import batched, zip_longest
from pathlib import Path

import yaml
from rich import print as print_rich
from rich.markup import escape as markup_escape

from bindiffscript import __version__


def print_diff(blobs: Sequence[bytes], width: int) -> None:
    """Prints a nice side by side diff of binary blobs"""

    def formatted(chunks: Sequence[Sequence[int]], width: int) -> str:
        """Returns a readable representation of a byte sequence already zipped
        with it's index"""
        result: tuple[list[str], ...] = tuple(
            [] for _ in range(len(chunks[0]))
        )
        for p in chunks:
            assert len(p) == len(result)
            color = "green" if all(c == p[0] for c in p) else "red"
            for i, c in enumerate(p):
                result[i].append(
                    f"[{color}]{c:02X}-{c:03}-{markup_escape(chr(c) if 32 <= c < 127 else '■' if c == 255 else '?')}[/]"
                    if c is not None
                    else "xx-xxx-x"
                )
        return " │ ".join(
            "|".join(c for c in r) + " " * (width - len(r)) * 9 for r in result
        )

    for blob in blobs:
        print(blob)

    for chunks in batched(zip_longest(*blobs), width):
        print_rich(formatted(chunks, width))


def bindiffscript(args: Args) -> None:
    """Magic happens here"""

    def padded_file_content(
        path: str, padding: None | Sequence[Sequence[int]]
    ) -> bytes:
        with Path(path).open("rb") as input_file:
            raw_data = bytearray(input_file.read())
            for index, amount, *rest in padding or []:
                padding_value = rest[0].to_bytes() if rest else b"\ff"
                raw_data[index:index] = padding_value * amount
            return bytes(raw_data)

    with args.file[0].open() as script_file:
        script = yaml.safe_load(script_file)

    print_diff(
        [
            padded_file_content(
                file["path"].replace("${here}", str(args.file[0].parent)),
                file.get("padding"),
            )[: args.head or script.get("head")]
            for file in script["files"]
        ],
        args.width or script.get("width", 8),
    )


def parse_args(argv: Sequence[str] | None = None) -> Args:
    """Boilerplate"""
    parser = ArgumentParser(__doc__)
    parser.add_argument("--version", action="store_true")
    parser.add_argument("--verbose", "-v", action="store_true")
    parser.add_argument(
        "--width",
        "-w",
        type=int,
        help="Amount of items/characters to show per line (defaults to 8)",
    )
    parser.add_argument(
        "--head",
        type=int,
        help="Show only <head> first bytes of each file",
    )
    parser.add_argument("file", type=Path, nargs="+")

    return parser.parse_args(argv)


def main() -> None:
    """Boilerplate"""
    args = parse_args()
    if args.version:
        print(__version__)
        return

    with suppress(KeyboardInterrupt):
        bindiffscript(args)


if __name__ == "__main__":
    main()
