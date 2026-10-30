"""Tests for platform log adapters using mocked native command output."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from unittest.mock import AsyncMock, patch

import pytest

from ghostwatch.core.schema import AvailabilityStatus

# --- Journal adapter ---

class TestJournalAdapter:
    @pytest.fixture
    def adapter(self):
        from ghostwatch.platforms.linux.journal import JournalAdapter
        return JournalAdapter()

    async def test_no_journalctl(self, adapter):
        with patch("shutil.which", return_value=None):
            events, cap = await adapter.collect()
        assert events == []
        assert cap.status == AvailabilityStatus.UNAVAILABLE

    async def test_valid_json_output(self, adapter):
        ts_micros = int(datetime(2026, 10, 29, 12, 0, 0, tzinfo=UTC).timestamp() * 1_000_000)
        entry = {
            "__REALTIME_TIMESTAMP": str(ts_micros),
            "MESSAGE": "sshd: accepted connection",
            "_PID": "1234",
            "_COMM": "sshd",
            "_EXE": "/usr/sbin/sshd",
            "SYSLOG_IDENTIFIER": "sshd",
            "PRIORITY": "6",
        }
        stdout = json.dumps(entry).encode() + b"\n"

        mock_proc = AsyncMock()
        mock_proc.returncode = 0
        mock_proc.communicate = AsyncMock(return_value=(stdout, b""))

        with patch("shutil.which", return_value="/usr/bin/journalctl"), \
             patch("asyncio.create_subprocess_exec", return_value=mock_proc):
            events, cap = await adapter.collect()

        assert len(events) == 1
        assert events[0].event_type == "journal.sshd"
        assert cap.status == AvailabilityStatus.OK

    async def test_permission_denied(self, adapter):
        mock_proc = AsyncMock()
        mock_proc.returncode = 1
        mock_proc.communicate = AsyncMock(return_value=(b"", b"Failed to open journal: Permission denied"))

        with patch("shutil.which", return_value="/usr/bin/journalctl"), \
             patch("asyncio.create_subprocess_exec", return_value=mock_proc):
            events, cap = await adapter.collect()

        assert events == []
        assert cap.status == AvailabilityStatus.PERMISSION_DENIED

    async def test_empty_output(self, adapter):
        mock_proc = AsyncMock()
        mock_proc.returncode = 0
        mock_proc.communicate = AsyncMock(return_value=(b"", b""))

        with patch("shutil.which", return_value="/usr/bin/journalctl"), \
             patch("asyncio.create_subprocess_exec", return_value=mock_proc):
            events, cap = await adapter.collect()

        assert events == []
        assert cap.status == AvailabilityStatus.OK


# --- Unified Log adapter ---

class TestUnifiedLogAdapter:
    @pytest.fixture
    def adapter(self):
        from ghostwatch.platforms.macos.unified_log import UnifiedLogAdapter
        return UnifiedLogAdapter()

    async def test_no_log_utility(self, adapter):
        with patch("shutil.which", return_value=None):
            events, cap = await adapter.collect()
        assert events == []
        assert cap.status == AvailabilityStatus.UNAVAILABLE

    async def test_valid_json_output(self, adapter):
        entries = [
            {
                "timestamp": "2026-10-29T12:00:00Z",
                "eventMessage": "Login window started",
                "messageType": "Default",
                "processID": 88,
                "process": "loginwindow",
                "senderImagePath": "/System/Library/CoreServices/loginwindow.app/loginwindow",
                "subsystem": "com.apple.loginwindow",
                "category": "session",
                "sender": "loginwindow",
            }
        ]
        stdout = json.dumps(entries).encode()

        mock_proc = AsyncMock()
        mock_proc.returncode = 0
        mock_proc.communicate = AsyncMock(return_value=(stdout, b""))

        with patch("shutil.which", return_value="/usr/bin/log"), \
             patch("asyncio.create_subprocess_exec", return_value=mock_proc):
            events, cap = await adapter.collect()

        assert len(events) == 1
        assert events[0].event_type == "unified_log.default"
        assert cap.status == AvailabilityStatus.OK

    async def test_private_redaction_noted(self, adapter):
        entries = [
            {
                "timestamp": "2026-10-29T12:00:00Z",
                "eventMessage": "User <private> logged in",
                "messageType": "Default",
                "processID": 10,
            }
        ]
        stdout = json.dumps(entries).encode()

        mock_proc = AsyncMock()
        mock_proc.returncode = 0
        mock_proc.communicate = AsyncMock(return_value=(stdout, b""))

        with patch("shutil.which", return_value="/usr/bin/log"), \
             patch("asyncio.create_subprocess_exec", return_value=mock_proc):
            events, cap = await adapter.collect()

        assert len(events) == 1
        assert cap.status == AvailabilityStatus.PARTIAL
        assert "private" in cap.note.lower()

    async def test_malformed_json_handled(self, adapter):
        mock_proc = AsyncMock()
        mock_proc.returncode = 0
        mock_proc.communicate = AsyncMock(return_value=(b"not json at all", b""))

        with patch("shutil.which", return_value="/usr/bin/log"), \
             patch("asyncio.create_subprocess_exec", return_value=mock_proc):
            events, cap = await adapter.collect()

        assert events == []
        assert cap.status == AvailabilityStatus.PARTIAL
