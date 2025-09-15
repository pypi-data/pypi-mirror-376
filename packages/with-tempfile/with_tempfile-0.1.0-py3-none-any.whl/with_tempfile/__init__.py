# SPDX-FileCopyrightText: Peter Pentchev <roam@ringlet.net>
# SPDX-License-Identifier: BSD-2-Clause
"""Create a temporary file, take care of removing it if needed.

The main purpose of this module is to provide a set of functions for
writing and appending data to a file in an atomic way by creating
a temporary file in the same directory and then renaming it over
the destination.
Currently it provides the `write_text` and `append_text` functions;
their `*_bytes` equivalents are planned.
"""

from __future__ import annotations

from .defs import VERSION
from .impl import append_text
from .impl import write_text
from .temputil import NamedTemporaryTextFile
from .temputil import TemporaryDirectory
from .temputil import TemporaryTextFile


__all__ = [
    "VERSION",
    "NamedTemporaryTextFile",
    "TemporaryDirectory",
    "TemporaryTextFile",
    "append_text",
    "write_text",
]
