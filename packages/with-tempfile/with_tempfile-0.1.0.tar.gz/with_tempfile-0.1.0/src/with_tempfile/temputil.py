# SPDX-FileCopyrightText: Peter Pentchev <roam@ringlet.net>
# SPDX-License-Identifier: BSD-2-Clause
"""Helpers that combine temporary files and pathlib routines.

This module defines the `NamedTemporaryTextFile` function and
the `TemporaryDirectory` class that parallel the corresponding
classes from the system `tempfile` module, but also have
the additional `path` and `resolved_path` fields.
The goal is to make it easier to use `pathlib.Path` objects
everywhere, while still using the system temporary file routines.
"""

from __future__ import annotations

import pathlib
import sys
import tempfile
import typing


if typing.TYPE_CHECKING:
    from typing import IO, Any, Final, Self

    from . import pathutil

    TempTextWrap = tempfile._TemporaryFileWrapper[str]  # noqa: SLF001  # we need it
    TempDir = tempfile.TemporaryDirectory[str]
else:
    TempTextWrap = tempfile._TemporaryFileWrapper  # noqa: SLF001  # we need it
    TempDir = tempfile.TemporaryDirectory


class TemporaryTextFile(TempTextWrap):
    """A named temporary file with a ready-made `pathlib.Path` path."""

    path: pathlib.Path
    """The path to the tempfile as a `pathlib.Path` object."""

    resolved_path: pathlib.Path
    """The resolved path to the tempfile as a `pathlib.Path` object."""

    if sys.version_info >= (3, 12):

        def __init__(
            self: Self,
            file: IO[str],
            name: str,
            delete: bool = True,  # noqa: FBT001,FBT002  # tempfile API
            delete_on_close: bool = True,  # noqa: FBT001,FBT002  # tempfile API
        ) -> None:
            """Create the temporary file, initialize our new fields."""
            super().__init__(file, name=name, delete=delete, delete_on_close=delete_on_close)
            self._setup_paths()
    else:

        def __init__(
            self: Self,
            file: IO[str],
            name: str,
            delete: bool = True,  # noqa: FBT001,FBT002  # tempfile API
        ) -> None:
            """Create the temporary file, initialize our new fields."""
            super().__init__(file, name=name, delete=delete)
            self._setup_paths()

    def __repr__(self) -> str:
        """Provide a Python-esque representation."""
        # Python 3.14 may evaluate `f"{self!r}"` in the constructor...
        if not hasattr(self, "path"):
            self._setup_paths()

        return (
            f"{type(self).__name__}(file={self.file!r}, name={self.name!r}, "
            f"path={self.path!r}, resolved_path={self.resolved_path!r}"
        )

    def _setup_paths(self) -> None:
        """Initialize our new fields."""
        self.path = pathlib.Path(self.name)
        self.resolved_path = self.path.resolve()

    def unset_delete(self, *, also_on_close: bool = True) -> None:
        """Unset the "delete on drop" and also possibly the "delete on close" flag.

        The caller took care of the file, e.g. renamed it, removed it, or passed it to
        another consumer to use as-is.
        """

        def handle(obj: Any) -> None:  # noqa: ANN401  # we can handle anything
            """Unset the `delete` and maybe the `delete_on_close` flags if they are there."""
            if hasattr(obj, "delete"):
                obj.delete = False
            if also_on_close and hasattr(obj, "delete_on_close"):
                obj.delete_on_close = False

        handle(self)

        match getattr(self, "_closer", None):
            case None:
                pass

            case closer:
                handle(closer)


def NamedTemporaryTextFile(  # noqa: N802,PLR0913  # tempfile-like API
    *,
    buffering: int = -1,
    dir: str | None = None,  # noqa: A002  # tempfile API
    encoding: str | None = None,
    prefix: str | None = None,
    suffix: str | None = None,
    delete: bool = True,
) -> TemporaryTextFile:
    """Create a temporary file that holds its path."""
    fd, name = tempfile.mkstemp(dir=dir, prefix=prefix, suffix=suffix, text=True)
    tempf: Final = open(  # noqa: PTH123,SIM115  # low-level; also, a file descriptor
        fd,
        mode="w+",
        buffering=buffering,
        encoding=encoding,
    )
    return TemporaryTextFile(tempf, name, delete=delete)


class TemporaryDirectory(TempDir):
    """A temporary directory with a ready-made `pathlib.Path` path.

    Note that the `__enter__()` method (and consequently `with TemporaryDirectory(...) as tempd:`)
    returns a `pathlib.Path` object instead of a string!
    """

    path: pathlib.Path
    """The path to the tempfile as a `pathlib.Path` object."""

    resolved_path: pathlib.Path
    """The resolved path to the tempfile as a `pathlib.Path` object."""

    if sys.version_info >= (3, 12):

        def __init__(
            self,
            suffix: str | None = None,
            prefix: str | None = None,
            dir: pathutil.PathLike | None = None,  # noqa: A002  # tempfile API
            ignore_cleanup_errors: bool = False,  # noqa: FBT001,FBT002  # tempfile API
            *,
            delete: bool = True,
        ) -> None:
            """Create the temporary directory, initialize our new fields."""
            super().__init__(
                suffix=suffix,
                prefix=prefix,
                dir=dir,
                ignore_cleanup_errors=ignore_cleanup_errors,
                delete=delete,
            )
            self._setup_paths()

    else:

        def __init__(
            self,
            suffix: str | None = None,
            prefix: str | None = None,
            dir: pathutil.PathLike | None = None,  # noqa: A002  # tempfile API
            ignore_cleanup_errors: bool = False,  # noqa: FBT001,FBT002  # tempfile API
        ) -> None:
            """Create the temporary directory, initialize our new fields."""
            super().__init__(
                suffix=suffix,
                prefix=prefix,
                dir=dir,
                ignore_cleanup_errors=ignore_cleanup_errors,
            )
            self._setup_paths()

    def _setup_paths(self) -> None:
        """Initialize our new fields."""
        self.path = pathlib.Path(self.name)
        self.resolved_path = self.path.resolve()

    def __enter__(self) -> pathlib.Path:  # type: ignore[override]
        """Enter a context, return the path to the directory.

        Note that this method returns a `pathlib.Path` object instead of a string!
        """
        return self.path
