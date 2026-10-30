"""Tests for SQLite event store."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from ghostwatch.core.schema import EventSource, GhostEvent
from ghostwatch.storage.database import EventStore


@pytest.fixture
async def store(tmp_path):
    s = EventStore(tmp_path / "test.db")
    await s.open()
    yield s
    await s.close()


def make_event(event_type: str = "process_new", summary: str = "test") -> GhostEvent:
    return GhostEvent(
        timestamp=datetime.now(tz=UTC),
        source=EventSource.PROCESS_SNAPSHOT,
        event_type=event_type,
        summary=summary,
    )


async def test_save_and_list(store):
    ev = make_event()
    saved = await store.save_event(ev)
    assert saved is True
    events = await store.list_events()
    assert len(events) == 1
    assert events[0].id == ev.id


async def test_deduplication(store):
    ev = make_event()
    await store.save_event(ev)
    await store.save_event(ev)
    # Second save of same ID must not add a duplicate
    events = await store.list_events()
    assert len(events) == 1


async def test_multiple_events_ordered(store):
    for i in range(5):
        await store.save_event(make_event(summary=f"event {i}"))
    events = await store.list_events()
    assert len(events) == 5


async def test_clear(store):
    await store.save_event(make_event())
    await store.save_event(make_event())
    deleted = await store.clear()
    assert deleted == 2
    events = await store.list_events()
    assert events == []


async def test_list_with_source_filter(store):
    ev_proc = make_event()
    ev_journal = GhostEvent(
        timestamp=datetime.now(tz=UTC),
        source=EventSource.JOURNAL,
        event_type="journal.sshd",
        summary="SSH login",
    )
    await store.save_event(ev_proc)
    await store.save_event(ev_journal)

    journal_events = await store.list_events(source="journal")
    assert len(journal_events) == 1
    assert journal_events[0].source == EventSource.JOURNAL
