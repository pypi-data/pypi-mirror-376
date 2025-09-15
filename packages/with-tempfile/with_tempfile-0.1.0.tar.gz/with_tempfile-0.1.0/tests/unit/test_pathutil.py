# SPDX-FileCopyrightText: Peter Pentchev <roam@ringlet.net>
# SPDX-License-Identifier: BSD-2-Clause
"""Test handling strings and `pathlib.Path` objects."""

from __future__ import annotations

import pathlib
import typing

import pytest

from with_tempfile import pathutil
from with_tempfile import temputil

from . import defs


if typing.TYPE_CHECKING:
    from collections.abc import Iterable
    from typing import Final


STRINGS: Final = [".", "something", "/", "/nonexistent", "/something/else"]
"""The paths to test as strings."""

PATHS: Final = [pathlib.Path(path) for path in STRINGS]
"""The paths to test as paths."""


@pytest.mark.parametrize("src", STRINGS)
def test_str_as_path(*, src: str) -> None:
    """Make sure strings are converted to `pathlib.Path` objects."""
    res: Final = pathutil.as_path(src)
    assert isinstance(res, pathlib.Path)
    assert res is not src  # type: ignore[comparison-overlap]  # that's kind of the point
    assert str(res) == src


@pytest.mark.parametrize("src", PATHS)
def test_path_as_path(*, src: pathlib.Path) -> None:
    """Make sure `pathlib.Path` objects are returned, exactly themselves."""
    res: Final = pathutil.as_path(src)
    assert isinstance(res, pathlib.Path)
    assert res is src


@pytest.mark.parametrize(
    ("encoding", "expected"),
    [
        (None, ("UTF-8", [])),
        ("string", ("string", [])),
        (("tuple",), ("tuple", [])),
        (("a", "real", "big", "tuple"), ("a", ["real", "big", "tuple"])),
        (["list"], ("list", [])),
        (["a", "real", "long", "list"], ("a", ["real", "long", "list"])),
        (iter(["iterator"]), ("iterator", [])),
        (iter(["a", "real", "long", "iterator"]), ("a", ["real", "long", "iterator"])),
        ((f"g{word}" for word in ("enerator",)), ("generator", [])),
        ((f"g{word}" for word in ("enerator", "oes", "ogogo")), ("generator", ["goes", "gogogo"])),
    ],
)
def test_encoding_tuple(
    *,
    encoding: str | Iterable[str] | None,
    expected: tuple[str, list[str]],
) -> None:
    """Make sure `encoding_tuple()` splits the elements correctly."""
    first, others = pathutil.encoding_tuple(encoding)
    assert (first, list(others)) == expected


@pytest.mark.parametrize(
    ("encoding", "expected"),
    [
        (None, (defs.WORD_STR, "UTF-8")),
        ("UTF-8", (defs.WORD_STR, "UTF-8")),
        (defs.ENC_SINGLE, (defs.WORD_SINGLE_STR, defs.ENC_SINGLE)),
        (("UTF-8",), (defs.WORD_STR, "UTF-8")),
        ((defs.ENC_SINGLE,), (defs.WORD_SINGLE_STR, defs.ENC_SINGLE)),
        (["UTF-8", defs.ENC_SINGLE], (defs.WORD_STR, "UTF-8")),
        ([defs.ENC_SINGLE, "UTF-8"], (defs.WORD_SINGLE_STR, defs.ENC_SINGLE)),
    ],
)
def test_read_text(*, encoding: str | Iterable[str] | None, expected: tuple[str, str]) -> None:
    """Make sure `read_text()` handles the specified encodings correctly."""
    with temputil.TemporaryDirectory(prefix="pathutil-test-") as tempd:
        tempf: Final = tempd / "a-file.txt"
        tempf.write_text(defs.WORD_STR)
        assert pathutil.read_text(tempf, encoding=encoding) == expected
