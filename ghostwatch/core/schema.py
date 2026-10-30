"""Shared event schema — every adapter emits GhostEvent instances."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field, field_validator, model_validator


class EventSource(StrEnum):
    PROCESS_SNAPSHOT = "process_snapshot"
    JOURNAL = "journal"
    UNIFIED_LOG = "unified_log"
    SAMPLE = "sample"


class Severity(StrEnum):
    INFO = "info"
    NOTICE = "notice"
    WARNING = "warning"
    HIGH = "high"


class AvailabilityStatus(StrEnum):
    OK = "ok"
    UNAVAILABLE = "unavailable"         # command/tool not present
    PERMISSION_DENIED = "permission_denied"
    PARTIAL = "partial"                 # some data, some redacted/missing


class ProcessInfo(BaseModel):
    pid: int | None = None
    ppid: int | None = None
    name: str | None = None
    exe: str | None = None              # None if inaccessible, not guessed
    cmdline: list[str] | None = None
    create_time: datetime | None = None
    username: str | None = None

    model_config = {"extra": "forbid"}


class RuleFinding(BaseModel):
    rule_id: str
    description: str
    matched_fields: dict[str, Any] = Field(default_factory=dict)

    model_config = {"extra": "forbid"}


class GhostEvent(BaseModel):
    """
    Normalised event emitted by every adapter.

    Fields are typed Optional where the underlying source may not supply them.
    Use None to mean 'not available', not '' or 0.
    """

    id: str = Field(default_factory=lambda: str(uuid4()))
    timestamp: datetime
    source: EventSource
    event_type: str                     # free-form label per source, e.g. "process_new"
    summary: str
    severity: Severity = Severity.INFO
    process: ProcessInfo | None = None
    evidence: dict[str, Any] = Field(default_factory=dict)
    rule_findings: list[RuleFinding] = Field(default_factory=list)
    availability: AvailabilityStatus = AvailabilityStatus.OK
    collection_note: str | None = None  # human-readable limitation note

    model_config = {"extra": "forbid"}

    @field_validator("timestamp", mode="before")
    @classmethod
    def ensure_utc(cls, v: Any) -> datetime:
        if isinstance(v, str):
            dt = datetime.fromisoformat(v)
        elif isinstance(v, (int, float)):
            dt = datetime.fromtimestamp(v, tz=UTC)
        else:
            dt = v
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=UTC)
        return dt

    @model_validator(mode="after")
    def summary_not_empty(self) -> GhostEvent:
        if not self.summary.strip():
            raise ValueError("summary must not be empty")
        return self


class CollectorCapability(BaseModel):
    """Reports what a collector was able (or unable) to do."""

    name: str
    status: AvailabilityStatus
    note: str | None = None

    model_config = {"extra": "forbid"}
