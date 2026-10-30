"""Tests for deterministic rules."""

from __future__ import annotations

from datetime import UTC, datetime

from ghostwatch.core.rules import apply_rules
from ghostwatch.core.schema import EventSource, GhostEvent, ProcessInfo, Severity


def make_event(**kwargs) -> GhostEvent:
    defaults = {
        "timestamp": datetime.now(tz=UTC),
        "source": EventSource.PROCESS_SNAPSHOT,
        "event_type": "process_new",
        "summary": "test",
    }
    defaults.update(kwargs)
    return GhostEvent(**defaults)


def test_no_findings_for_normal_process():
    ev = make_event(process=ProcessInfo(pid=100, name="nginx", exe="/usr/sbin/nginx"))
    result = apply_rules(ev)
    assert result.rule_findings == []
    assert result.severity == Severity.INFO


def test_temp_dir_rule_fires():
    ev = make_event(process=ProcessInfo(pid=200, name="sh", exe="/tmp/evil.sh"))
    result = apply_rules(ev)
    rule_ids = [f.rule_id for f in result.rule_findings]
    assert "PROC_TEMP_DIR" in rule_ids


def test_temp_dir_rule_private_tmp():
    ev = make_event(process=ProcessInfo(pid=201, name="python3", exe="/private/tmp/run.py"))
    result = apply_rules(ev)
    assert any(f.rule_id == "PROC_TEMP_DIR" for f in result.rule_findings)


def test_hidden_process_name_rule():
    ev = make_event(process=ProcessInfo(pid=300, name=".ghost", exe="/var/tmp/.ghost"))
    result = apply_rules(ev)
    rule_ids = [f.rule_id for f in result.rule_findings]
    assert "PROC_HIDDEN_NAME" in rule_ids
    assert "PROC_TEMP_DIR" in rule_ids  # also fires for /var/tmp


def test_interpreter_network_cmdline_rule():
    ev = make_event(
        process=ProcessInfo(
            pid=400,
            name="python3",
            cmdline=["python3", "-c", "import requests; requests.get('https://evil.com')"],
        )
    )
    result = apply_rules(ev)
    assert any(f.rule_id == "INTERP_NETWORK_CMDLINE" for f in result.rule_findings)


def test_severity_promoted_when_rule_fires():
    ev = make_event(
        severity=Severity.INFO,
        process=ProcessInfo(pid=500, name="sh", exe="/tmp/x.sh"),
    )
    result = apply_rules(ev)
    assert result.severity != Severity.INFO  # must be promoted


def test_high_severity_log_rule():
    ev = make_event(severity=Severity.HIGH)
    result = apply_rules(ev)
    assert any(f.rule_id == "HIGH_SEVERITY_LOG" for f in result.rule_findings)


def test_rule_does_not_modify_original():
    ev = make_event(process=ProcessInfo(pid=600, name="sh", exe="/tmp/x.sh"))
    _ = apply_rules(ev)
    # Original must be unchanged
    assert ev.rule_findings == []
