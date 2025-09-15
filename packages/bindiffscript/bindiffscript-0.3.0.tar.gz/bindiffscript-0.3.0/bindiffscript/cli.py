#!/usr/bin/env python3
#
# bindiffscript - insertion/offset aware binary diff
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
from rich.text import Text

from bindiffscript import __version__

Character = tuple[int, int]


def char_view_width(char_format: str) -> int:
    """Returns length (width) of one character visualization"""
    return len(Text.from_markup(format_character(0, 0, char_format, "red")))


def format_character(
    index: int, char: int, char_format: str, color: str
) -> str:
    """Turns one indexed character into something colorful"""
    return char_format.format(
        index=index,
        char=char,
        color=color,
        char_ascii=markup_escape(
            chr(char) if 32 <= char < 127 else "■" if char == 255 else "?"
        ),
    )


def print_diff(
    blobs: Sequence[Sequence[None | Character]],
    width: int,
    char_format: str,
    colors: tuple[str, str],
    context: None | int,
) -> None:
    """Prints a nice side by side diff of binary blobs"""

    def all_chars_equal(chars: Sequence[None | Character]) -> bool:
        return all(
            (c if c is None else c[1])
            == (chars[0] if chars[0] is None else chars[0][1])
            for c in chars[1:]
        )

    def formatted(
        chunk_line: Sequence[Sequence[None | Character]],
        char_format: str,
        width: int,
        pad_char: str,
    ) -> str:
        """Returns a readable representation of a byte sequence already zipped
        with it's index"""
        result: tuple[list[str], ...] = tuple(
            [] for _ in range(len(chunk_line[0]))
        )
        for p in chunk_line:
            assert len(p) == len(result)
            char_equal = all_chars_equal(p)
            for blob_index, c in enumerate(p):
                result[blob_index].append(
                    format_character(
                        c[0],
                        c[1],
                        char_format,
                        colors[0] if char_equal else colors[1],
                    )
                    if c is not None
                    else pad_char
                )
        return " │ ".join(
            "|".join(c for c in r)
            + " " * (width - len(r)) * (len(pad_char) + 1)
            for r in result
        )

    pad_char = char_view_width(char_format) * "-"
    lines = list(batched(zip_longest(*blobs), width))
    switches: set[int] = set()
    diff_in_line: set[int] = set()
    for i, line in enumerate(lines):
        if not all(all_chars_equal(p) for p in line):
            diff_in_line.add(i)
            if context is not None:
                for c in range(-context, 1 + context):
                    switches.add(max(0, min(len(lines) - 1, i + c)))

    last_line_printed = True
    idx_width = len(str(max(0 if b[-1] is None else b[-1][0] for b in blobs)))
    blob_view_width = (char_view_width(char_format) + 1) * width - 2

    for i, chunk_line in enumerate(lines):
        if context is None or i in switches:
            if not last_line_printed:
                print_rich(f"{'.' * idx_width} │ {' ' * blob_view_width} │")
            print_rich(
                f"[on {'gray100' if i in diff_in_line else 'gray89'} black]"
                f"{i:0{idx_width}}"
                f" │{formatted(chunk_line, char_format, width, pad_char)}[/]"
            )
        last_line_printed = context is None or i in switches


def bindiffscript(args: Args) -> None:
    """Magic happens here"""

    def padded_file_content(
        path: str, padding: None | Sequence[Sequence[int]]
    ) -> Sequence[None | Character]:
        with Path(path).open("rb") as input_file:
            raw_data: list[None | Character] = list(
                enumerate(input_file.read())
            )
            for index, amount, *_rest in sorted(
                padding or [], key=lambda x: x[0], reverse=True
            ):
                raw_data[index:index] = [None] * amount
            return raw_data

    with args.file[0].open() as script_file:
        script = yaml.safe_load(script_file)

    blobs = [
        padded_file_content(
            file["path"].replace("${here}", str(args.file[0].parent)),
            file.get("padding"),
        )[: args.head or script.get("head")]
        for file in script["files"]
    ]

    max_idx = max(0 if b[-1] is None else b[-1][0] for b in blobs)
    char_format = (
        script.get("format", "%ix-%x-%d-%a")
        .replace("%ix", f"[{{color}}]{{index:0{len(str(max_idx))}X}}[/]")
        .replace("%i", f"[{{color}}]{{index:0{len(format(max_idx, 'X'))}}}[/]")
        .replace("%x", "[{color}]{char:02X}[/]")
        .replace("%d", "[{color}]{char:03}[/]")
        .replace("%a", "[{color}]{char_ascii}[/]")
    )
    line_width = args.width or script.get("width", 8)
    blob_view_width = (char_view_width(char_format) + 1) * line_width - 2
    print_rich(
        f"{' ' * len(str(max_idx))} │ {' │ '.join(f'[bold]{file["path"]:<{blob_view_width}}[/]' for file in script['files'])}"
    )
    print_diff(
        blobs,
        line_width,
        char_format,
        script.get("colors", ("blue", "red")),
        args.context or script.get("context"),
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
        "--context",
        type=int,
        help="Show @context lines around mismatching lines",
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
