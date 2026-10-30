"""Tests for platform detection and adapter selection."""

from __future__ import annotations

import sys
from unittest.mock import patch

from ghostwatch.platforms.detect import current_platform, get_log_adapter


def test_macos_detection():
    with patch.object(sys, "platform", "darwin"):
        assert current_platform() == "macos"


def test_linux_detection():
    with patch.object(sys, "platform", "linux"):
        assert current_platform() == "linux"


def test_unsupported_platform():
    with patch.object(sys, "platform", "win32"):
        assert current_platform() == "unsupported"


def test_linux_adapter_returned():
    with patch.object(sys, "platform", "linux"):
        adapter = get_log_adapter()
        from ghostwatch.platforms.linux.journal import JournalAdapter
        assert isinstance(adapter, JournalAdapter)


def test_macos_adapter_returned():
    with patch.object(sys, "platform", "darwin"):
        adapter = get_log_adapter()
        from ghostwatch.platforms.macos.unified_log import UnifiedLogAdapter
        assert isinstance(adapter, UnifiedLogAdapter)


def test_unsupported_returns_none():
    with patch.object(sys, "platform", "win32"):
        adapter = get_log_adapter()
        assert adapter is None
