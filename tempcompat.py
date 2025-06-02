# SPDX-License-Identifier: Apache-2.0
"""tempcompat.py - compatibility helper for tempfile.TemporaryDirectory.

Provides a drop-in replacement that always accepts the ``delete`` keyword so
call sites can simply write ``TemporaryDirectory(delete=False)`` regardless of
whether they're running on Python < 3.12 or ≥ 3.12.
"""
from __future__ import annotations

import sys
import tempfile
from typing import Optional

__all__ = ["TemporaryDirectory"]

if sys.version_info >= (3, 12):
    # The standard library version already supports the ``delete`` parameter.
    TemporaryDirectory = tempfile.TemporaryDirectory  # type: ignore
else:

    class TemporaryDirectory(tempfile.TemporaryDirectory):  # type: ignore[misc]
        """Back-port of Python 3.12+ ``TemporaryDirectory`` ``delete`` support."""

        def __init__(
            self,
            *,
            suffix: Optional[str] = None,
            prefix: Optional[str] = None,
            dir: Optional[str] = None,
            ignore_cleanup_errors: bool = False,
            delete: bool = True,
        ) -> None:
            self._delete = delete
            # Call parent without the ``delete`` kwarg (not supported <3.12).
            super().__init__(
                suffix=suffix,
                prefix=prefix,
                dir=dir,
                ignore_cleanup_errors=ignore_cleanup_errors,
            )

        def cleanup(self) -> None:  # type: ignore[override]
            """Conditionally remove the directory respecting *delete*."""
            if self._delete:
                super().cleanup()
