# SPDX-FileCopyrightText: Peter Pentchev <roam@ringlet.net>
# SPDX-License-Identifier: BSD-2-Clause
"""Test core functionality: overwriting files and appending to them."""

from __future__ import annotations

import itertools
import typing

import pytest

import with_tempfile
from with_tempfile import temputil

from . import defs


if typing.TYPE_CHECKING:
    import pathlib
    from typing import Final


@pytest.mark.parametrize(
    ("before", "after", "encoding"),
    itertools.product(
        [None, "", "\n", "something\n", "нещо\n"],
        ["", "\n", "something else\n", "нещо друго\n"],
        [None, *defs.WORD_ENCODINGS],
    ),
)
def test_write_text(*, before: str | None, after: str, encoding: str | None) -> None:
    """Replace a file with one containing exactly the specified text."""

    def maybe_create(fpath: pathlib.Path) -> tuple[int, int] | None:
        """Create the file if we should, return the device and inode number."""
        if before is None:
            return None

        fpath.write_text(before, encoding=encoding)
        fstat: Final = fpath.stat()
        return fstat.st_dev, fstat.st_ino

    # Huh, we should have a TemporaryDirectory wrapper too, should we not?
    with temputil.TemporaryDirectory(prefix="test-with-tempfile-") as tempd:
        fpath: Final = tempd / "something.txt"
        prev_dev_inode: Final = maybe_create(fpath)

        with_tempfile.write_text(fpath, after, encoding=encoding)
        assert fpath.is_file()
        assert fpath.read_text(encoding=encoding) == after
        if prev_dev_inode is not None:
            fstat: Final = fpath.stat()
            assert (fstat.st_dev, fstat.st_ino) != prev_dev_inode


@pytest.mark.parametrize(
    ("before", "more", "encoding"),
    itertools.product(
        [None, "", "\n", "something\n", "нещо\n"],
        ["", "\n", "something else\n", "нещо друго\n"],
        [None, *defs.WORD_ENCODINGS],
    ),
)
def test_append_text(*, before: str | None, more: str, encoding: str | None) -> None:
    """Replace a file with one containing exactly the specified text."""

    def maybe_create(fpath: pathlib.Path) -> tuple[int, int] | None:
        """Create the file if we should, return the device and inode number."""
        if before is None:
            return None

        fpath.write_text(before, encoding=encoding)
        fstat: Final = fpath.stat()
        return fstat.st_dev, fstat.st_ino

    with temputil.TemporaryDirectory(prefix="test-with-tempfile-") as tempd:
        fpath: Final = tempd / "something.txt"
        prev_dev_inode: Final = maybe_create(fpath)

        with_tempfile.append_text(fpath, more, encoding=encoding)
        assert fpath.is_file()
        assert fpath.read_text(encoding=encoding) == ("" if before is None else before) + more
        if prev_dev_inode is not None:
            fstat: Final = fpath.stat()
            assert (fstat.st_dev, fstat.st_ino) != prev_dev_inode


def test_append_text_detect_encoding() -> None:
    """Replace a file after guessing its encoding."""
    with temputil.TemporaryDirectory(prefix="test-with-tempfile-") as tempd:
        fpath: Final = tempd / "something.txt"
        fpath.write_text(defs.WORD_STR, encoding=defs.ENC_SINGLE)
        fstat_before: Final = fpath.stat()

        with pytest.raises(UnicodeDecodeError):
            with_tempfile.append_text(fpath, "\n")

        with pytest.raises(UnicodeDecodeError):
            with_tempfile.append_text(fpath, "\n", encoding="UTF-8")

        with_tempfile.append_text(fpath, "\n", encoding=defs.WORD_ENCODINGS_ALL)

        with pytest.raises(UnicodeDecodeError):
            fpath.read_text()

        with pytest.raises(UnicodeDecodeError):
            fpath.read_text(encoding="UTF-8")

        assert fpath.read_text(encoding=defs.ENC_SINGLE) == f"{defs.WORD_STR}\n"
        fstat_after: Final = fpath.stat()
        assert fstat_before.st_dev == fstat_after.st_dev
        assert fstat_before.st_ino != fstat_after.st_ino
