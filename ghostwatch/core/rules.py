"""Deterministic rules applied before AI inference.

Each rule inspects a GhostEvent and, if triggered, appends a RuleFinding.
Rules never modify evidence; they only annotate.
"""

from __future__ import annotations

import re
from collections.abc import Callable

from ghostwatch.core.schema import GhostEvent, RuleFinding, Severity

# Directories considered suspicious for executable launchers
_TEMP_DIRS = re.compile(
    r"^(/tmp|/var/tmp|/dev/shm|/private/tmp|"
    r"/Users/[^/]+/Downloads|/Users/[^/]+/Library/Caches)",
    re.IGNORECASE,
)

_KNOWN_INTERPRETERS = frozenset(
    {"python", "python3", "ruby", "perl", "bash", "sh", "zsh", "node", "php"}
)

RuleFunc = Callable[[GhostEvent], list[RuleFinding]]

_REGISTRY: list[RuleFunc] = []


def rule(fn: RuleFunc) -> RuleFunc:
    _REGISTRY.append(fn)
    return fn


@rule
def rule_process_from_temp(event: GhostEvent) -> list[RuleFinding]:
    """Flag processes whose executable lives in a temporary or downloads directory."""
    if not event.process or not event.process.exe:
        return []
    if _TEMP_DIRS.match(event.process.exe):
        return [
            RuleFinding(
                rule_id="PROC_TEMP_DIR",
                description=(
                    "Process launched from a temporary or downloads directory. "
                    "Legitimate software rarely executes from these locations."
                ),
                matched_fields={"exe": event.process.exe},
            )
        ]
    return []


@rule
def rule_interpreter_with_network_cmdline(event: GhostEvent) -> list[RuleFinding]:
    """Flag interpreter processes whose command line references common download tools."""
    if not event.process:
        return []
    name = (event.process.name or "").lower()
    if name not in _KNOWN_INTERPRETERS:
        return []
    cmdline = " ".join(event.process.cmdline or []).lower()
    download_keywords = {"curl", "wget", "http://", "https://", "requests.get", "urllib"}
    matched = [kw for kw in download_keywords if kw in cmdline]
    if matched:
        return [
            RuleFinding(
                rule_id="INTERP_NETWORK_CMDLINE",
                description=(
                    "Interpreter process command line contains network-related keywords. "
                    "May indicate a download-and-execute pattern."
                ),
                matched_fields={"name": name, "matched_keywords": matched},
            )
        ]
    return []


@rule
def rule_hidden_process_name(event: GhostEvent) -> list[RuleFinding]:
    """Flag processes whose name starts with a dot (Unix hidden-file convention)."""
    if not event.process or not event.process.name:
        return []
    if event.process.name.startswith("."):
        return [
            RuleFinding(
                rule_id="PROC_HIDDEN_NAME",
                description=(
                    "Process name begins with a dot, mimicking the Unix hidden-file "
                    "convention. This is unusual for running processes."
                ),
                matched_fields={"name": event.process.name},
            )
        ]
    return []


@rule
def rule_high_severity_log(event: GhostEvent) -> list[RuleFinding]:
    """Promote log events that already carry a high-severity label."""
    if event.severity == Severity.HIGH and not event.rule_findings:
        return [
            RuleFinding(
                rule_id="HIGH_SEVERITY_LOG",
                description="Source log entry was already rated high severity.",
                matched_fields={"source": event.source, "summary": event.summary[:120]},
            )
        ]
    return []


def apply_rules(event: GhostEvent) -> GhostEvent:
    """
    Apply all registered rules to *event*.

    Returns a new GhostEvent with rule_findings populated.
    Rules do not mutate evidence; they only append findings.
    """
    findings: list[RuleFinding] = list(event.rule_findings)
    for rule_fn in _REGISTRY:
        findings.extend(rule_fn(event))

    # Promote severity when any rule fires
    if findings and event.severity == Severity.INFO:
        new_severity = Severity.NOTICE
    else:
        new_severity = event.severity

    return event.model_copy(update={"rule_findings": findings, "severity": new_severity})
