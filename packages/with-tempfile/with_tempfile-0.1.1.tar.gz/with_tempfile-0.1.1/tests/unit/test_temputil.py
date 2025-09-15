# SPDX-FileCopyrightText: Peter Pentchev <roam@ringlet.net>
# SPDX-License-Identifier: BSD-2-Clause
"""Test some basic functionality: creating temporary files."""

from __future__ import annotations

import itertools
import pathlib
import sys
import typing

import pytest

from with_tempfile import temputil

from . import defs


if typing.TYPE_CHECKING:
    from typing import Final


def validate_name_and_path(  # noqa: PLR0913
    name: str,
    path: pathlib.Path,
    resolved_path: pathlib.Path,
    *,
    prefix: str | None,
    suffix: str | None,
    curdir: bool,
    cwd: pathlib.Path,
) -> None:
    """Make sure the name and path of the new object are correct."""
    assert name.removeprefix("./") == str(path)

    if prefix is not None:
        assert path.name.startswith(prefix)
    if suffix is not None:
        assert path.name.endswith(suffix)

    if curdir:
        assert resolved_path.parent == cwd
    else:
        with pytest.raises(ValueError, match=str(cwd)):
            resolved_path.relative_to(cwd)


@pytest.mark.parametrize(
    ("encoding", "prefix", "suffix", "curdir", "delete"),
    itertools.product(
        [None, *defs.WORD_ENCODINGS],
        [None, "some-", "", "..."],
        [None, ".txt", "-whee", "..."],
        [False, True],
        [False, True],
    ),
)
def test_create_text(
    *,
    encoding: str | None,
    prefix: str | None,
    suffix: str | None,
    curdir: bool,
    delete: bool,
) -> None:
    """Create some files, check their attributes."""
    print()
    cwd: Final = pathlib.Path.cwd()
    to_remove: Final[list[pathlib.Path]] = []

    def create() -> temputil.TemporaryTextFile:
        """Create a single text file."""
        tempf: Final = temputil.NamedTemporaryTextFile(
            encoding=encoding,
            prefix=prefix,
            suffix=suffix,
            dir="." if curdir else None,
            delete=delete,
        )
        if not delete:
            to_remove.append(tempf.path)
        print(f"Got file {tempf!r} name {tempf.name} path {tempf.path!r}")

        assert tempf.path.is_file()
        assert tempf.resolved_path.is_file()

        validate_name_and_path(
            tempf.name,
            tempf.path,
            tempf.resolved_path,
            prefix=prefix,
            suffix=suffix,
            curdir=curdir,
            cwd=cwd,
        )

        print(defs.WORD_STR, file=tempf, end="", flush=True)
        assert (
            tempf.path.read_bytes() == defs.WORD_STR.encode(encoding)
            if encoding is not None
            else defs.WORD_STR.encode()
        )

        return tempf

    def create_and_maybe_remove() -> set[pathlib.Path]:
        """Create some text files, make sure they are there, remove them."""
        files: Final = [create() for _ in range(10)]
        assert len({tempf.name for tempf in files}) == len(files)
        assert len({tempf.path for tempf in files}) == len(files)
        assert len({tempf.resolved_path for tempf in files}) == len(files)

        for tempf in files:
            assert tempf.path.is_file()
            assert tempf.resolved_path.is_file()

        return {tempf.resolved_path for tempf in files}

    try:
        paths: Final = create_and_maybe_remove()
        for path in paths:
            if delete:
                assert not path.is_symlink()
                assert not path.exists()
            else:
                assert path.is_file()
    finally:
        not_removed: Final = []
        for path in to_remove:
            print(f"Cleaning up {path}")
            try:
                path.unlink()
            except OSError as err:
                not_removed.append(path)
                print(f"Could not remove {path}: {err}", file=sys.stderr)

        assert not not_removed

        assert delete == (not to_remove)


@pytest.mark.parametrize(
    ("prefix", "suffix", "curdir", "delete"),
    itertools.product(
        [None, "some-", "", "..."],
        [None, ".txt", "-whee", "..."],
        [False, True],
        [False, True] if sys.version_info >= (3, 12) else [True],
    ),
)
def test_temporary_directory(
    *,
    prefix: str | None,
    suffix: str | None,
    curdir: bool,
    delete: bool,
) -> None:
    """Create some files, check their attributes."""
    print()
    cwd: Final = pathlib.Path.cwd()
    to_remove: Final[list[pathlib.Path]] = []

    def create() -> temputil.TemporaryDirectory:
        """Create a single text file."""
        if sys.version_info >= (3, 12):
            tempd = temputil.TemporaryDirectory(
                prefix=prefix,
                suffix=suffix,
                dir="." if curdir else None,
                delete=delete,
            )
        else:
            tempd = temputil.TemporaryDirectory(
                prefix=prefix,
                suffix=suffix,
                dir="." if curdir else None,
            )
        if not delete:
            to_remove.append(tempd.path)
        print(f"Got dir {tempd!r} name {tempd.name} path {tempd.path!r}")

        assert tempd.path.is_dir()
        assert tempd.resolved_path.is_dir()

        validate_name_and_path(
            tempd.name,
            tempd.path,
            tempd.resolved_path,
            prefix=prefix,
            suffix=suffix,
            curdir=curdir,
            cwd=cwd,
        )

        return tempd

    def create_and_maybe_remove() -> set[pathlib.Path]:
        """Create some text files, make sure they are there, remove them."""
        dirs: Final = [create() for _ in range(10)]
        assert len({tempd.name for tempd in dirs}) == len(dirs)
        assert len({tempd.path for tempd in dirs}) == len(dirs)
        assert len({tempd.resolved_path for tempd in dirs}) == len(dirs)

        for tempd in dirs:
            assert tempd.path.is_dir()
            assert tempd.resolved_path.is_dir()

        return {tempd.resolved_path for tempd in dirs}

    try:
        paths: Final = create_and_maybe_remove()
        for path in paths:
            if delete:
                assert not path.is_symlink()
                assert not path.exists()
            else:
                assert path.is_dir()
    finally:
        not_removed: Final = []
        for path in to_remove:
            print(f"Cleaning up {path}")
            try:
                path.rmdir()
            except OSError as err:
                not_removed.append(path)
                print(f"Could not remove {path}: {err}", file=sys.stderr)

        assert not not_removed

        assert delete == (not to_remove)
