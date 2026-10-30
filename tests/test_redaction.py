"""Tests for the redaction module."""

from __future__ import annotations

from datetime import UTC, datetime

from ghostwatch.core.redact import redact_event
from ghostwatch.core.schema import EventSource, GhostEvent, ProcessInfo


def make_event(**kwargs) -> GhostEvent:
    defaults = {
        "timestamp": datetime.now(tz=UTC),
        "source": EventSource.PROCESS_SNAPSHOT,
        "event_type": "process_new",
        "summary": "test",
    }
    defaults.update(kwargs)
    return GhostEvent(**defaults)


def test_no_secrets_unchanged():
    ev = make_event(process=ProcessInfo(pid=1, cmdline=["nginx", "-g", "daemon off;"]))
    result = redact_event(ev)
    assert result.process.cmdline == ["nginx", "-g", "daemon off;"]


def test_token_in_cmdline_redacted():
    ev = make_event(
        process=ProcessInfo(
            pid=1,
            cmdline=["curl", "--header", "Authorization: Bearer sk-abc123xyz456", "https://api.example.com"],
        )
    )
    result = redact_event(ev)
    joined = " ".join(result.process.cmdline)
    assert "sk-abc123xyz456" not in joined
    assert "[REDACTED]" in joined


def test_password_flag_redacted():
    ev = make_event(
        process=ProcessInfo(pid=2, cmdline=["mysql", "--password=supersecret"])
    )
    result = redact_event(ev)
    joined = " ".join(result.process.cmdline)
    assert "supersecret" not in joined


def test_evidence_dict_secret_redacted():
    ev = make_event(evidence={"api_key": "sk-abc123", "host": "localhost"})
    result = redact_event(ev)
    assert "sk-abc123" not in str(result.evidence)
    assert result.evidence.get("host") == "localhost"


def test_original_not_mutated():
    ev = make_event(
        process=ProcessInfo(pid=3, cmdline=["python3", "--token=secret999"])
    )
    _ = redact_event(ev)
    assert "secret999" in " ".join(ev.process.cmdline)  # original unchanged
