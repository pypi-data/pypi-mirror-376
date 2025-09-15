# SPDX-FileCopyrightText: Peter Pentchev <roam@ringlet.net>
# SPDX-License-Identifier: BSD-2-Clause
"""Helpers for manipulating `pathlib.Path` objects and strings.

This module's main purpose is to define the `PathLike` type that
may be used for function arguments that may be of any type suitable
for passing to the system Python file handling routines.
It is somewhat similar to the `os.PathLike` class, but it has
a different set of allowed classes, e.g. it allows strings.
"""

from __future__ import annotations

import pathlib
import typing


if typing.TYPE_CHECKING:
    from collections.abc import Iterable, Iterator
    from typing import Final


PathLike = pathlib.Path | str
"""Something that may be used as a path."""


def as_path(path: PathLike) -> pathlib.Path:
    """Convert a pathlike object to a path as needed."""
    if isinstance(path, pathlib.Path):
        return path

    return pathlib.Path(path)


def encoding_tuple(encoding: str | Iterable[str] | None) -> tuple[str, Iterator[str]]:
    """Split the first of the requested encoding names from the rest."""
    if encoding is None:
        return "UTF-8", iter(())

    if isinstance(encoding, str):
        return encoding, iter(())

    it: Final = iter(encoding)
    first: Final = next(it)
    return first, it


def read_text(path: pathlib.Path, *, encoding: str | Iterable[str] | None) -> tuple[str, str]:
    """Read a file's contents, try to decode it using the specified encodings in order.

    The return value is a tuple containing the full text read from the file and
    the name of the encoding used to decode it.

    The `encoding` parameter may be either None, a string, or an iterable of strings.
    In the latter case the specified encodings are tried in order; the first one that
    successfully decodes the file's contents is returned.
    """
    first, rest = encoding_tuple(encoding)
    raw: Final = path.read_bytes()
    try:
        return raw.decode(first), first
    except ValueError:
        for enc in rest:
            try:
                return raw.decode(enc), enc
            except ValueError:
                pass

        # None of the encodings worked, return the error from the first attempt
        raise
