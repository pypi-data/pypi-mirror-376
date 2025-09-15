# SPDX-FileCopyrightText: Peter Pentchev <roam@ringlet.net>
# SPDX-License-Identifier: BSD-2-Clause
"""Common definitions for the `with-tempfile` unit tests."""

from __future__ import annotations

import typing


if typing.TYPE_CHECKING:
    from typing import Final


WORD_STR: Final = "мррмот"
"""A string to write to the file."""

ENC_SINGLE: Final = "windows-1251"
"""The single-byte encoding to test with."""

ENC_SINGLE_LIMITED: Final = "us-ascii"
"""A single-byte encoding that does not recognize all byte values."""

WORD_SINGLE_STR: Final = WORD_STR.encode("UTF-8").decode(ENC_SINGLE)
"""The string re-encoded into the single-byte encoding."""

WORD_ENCODINGS: Final = ["UTF-8", ENC_SINGLE]
"""The encodings to test for."""

WORD_ENCODINGS_ALL: Final = ["UTF-8", ENC_SINGLE_LIMITED, ENC_SINGLE]
"""The encodings to test for, including the one that can't recognize Cyrillic text."""
