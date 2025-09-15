# SPDX-FileCopyrightText: Peter Pentchev <roam@ringlet.net>
# SPDX-License-Identifier: BSD-2-Clause
"""Common definitions for the with-tempfile library."""

from __future__ import annotations

import typing


if typing.TYPE_CHECKING:
    from typing import Final


VERSION: Final = "0.1.0"
"""The project version, semver-like."""
