# SPDX-FileCopyrightText: Peter Pentchev <roam@ringlet.net>
# SPDX-License-Identifier: BSD-2-Clause
"""The actual implementation of some classes and helper functions."""

from __future__ import annotations

import typing

from . import pathutil
from . import temputil


if typing.TYPE_CHECKING:
    from collections.abc import Iterable


def write_text(fpath: pathutil.PathLike, contents: str, *, encoding: str | None = None) -> None:
    """Atomically write the specified text to the specified file."""
    with temputil.NamedTemporaryTextFile(
        dir=str(pathutil.as_path(fpath).parent),
        encoding=encoding,
    ) as tempf:
        print(contents, end="", file=tempf, flush=True)
        tempf.path.rename(fpath)
        tempf.unset_delete()


def append_text(
    fpath: pathutil.PathLike,
    contents: str,
    *,
    encoding: str | Iterable[str] | None = None,
) -> None:
    """If the file exists, atomically append text, otherwise write the new contents."""
    try:
        current, actual_encoding = pathutil.read_text(pathutil.as_path(fpath), encoding=encoding)
    except FileNotFoundError:
        current, actual_encoding = "", pathutil.encoding_tuple(encoding)[0]

    write_text(fpath, f"{current}{contents}", encoding=actual_encoding)
