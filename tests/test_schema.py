"""Tests for the shared event schema."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from ghostwatch.core.schema import (
    AvailabilityStatus,
    EventSource,
    GhostEvent,
    ProcessInfo,
    Severity,
)


def make_event(**kwargs) -> GhostEvent:
    defaults = {
        "timestamp": datetime.now(tz=UTC),
        "source": EventSource.PROCESS_SNAPSHOT,
        "event_type": "process_new",
        "summary": "test event",
    }
    defaults.update(kwargs)
    return GhostEvent(**defaults)


def test_basic_event_creation():
    ev = make_event()
    assert ev.source == EventSource.PROCESS_SNAPSHOT
    assert ev.severity == Severity.INFO
    assert ev.availability == AvailabilityStatus.OK
    assert ev.id  # auto-generated


def test_empty_summary_rejected():
    with pytest.raises(ValidationError):
        make_event(summary="")


def test_whitespace_only_summary_rejected():
    with pytest.raises(ValidationError):
        make_event(summary="   ")


def test_naive_timestamp_becomes_utc():
    naive = datetime(2026, 10, 29, 12, 0, 0)
    ev = make_event(timestamp=naive)
    assert ev.timestamp.tzinfo is not None


def test_unix_timestamp_accepted():
    ev = make_event(timestamp=1700000000)
    assert ev.timestamp.tzinfo is not None


def test_process_info_optional_fields():
    pi = ProcessInfo(pid=1234)
    assert pi.name is None
    assert pi.exe is None


def test_event_with_process():
    ev = make_event(
        process=ProcessInfo(pid=99, name="bash", exe="/bin/bash")
    )
    assert ev.process.pid == 99


def test_sample_events_fixture_valid():
    """All events in the sample fixture must be valid GhostEvents."""
    import json
    from pathlib import Path

    fixture = Path(__file__).parent / "fixtures/sample_events.json"
    raw = json.loads(fixture.read_text())
    for item in raw:
        ev = GhostEvent.model_validate(item)
        assert ev.id
