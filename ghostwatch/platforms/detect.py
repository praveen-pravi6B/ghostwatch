"""Detect the current OS and return the appropriate log adapter."""

from __future__ import annotations

import sys


def current_platform() -> str:
    """Return 'macos', 'linux', or 'unsupported'."""
    s = sys.platform
    if s == "darwin":
        return "macos"
    if s.startswith("linux"):
        return "linux"
    return "unsupported"


def get_log_adapter():  # type: ignore[return]
    """
    Return the platform-specific log adapter instance.

    Imports are deferred so Linux-only tools are never loaded on macOS and vice versa.
    """
    p = current_platform()
    if p == "linux":
        from ghostwatch.platforms.linux.journal import JournalAdapter  # noqa: PLC0415

        return JournalAdapter()
    if p == "macos":
        from ghostwatch.platforms.macos.unified_log import UnifiedLogAdapter  # noqa: PLC0415

        return UnifiedLogAdapter()
    return None
