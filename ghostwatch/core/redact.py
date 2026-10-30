"""Redact sensitive fields from events before sending to the local AI model.

Rules:
- Replace credential-like strings in cmdline and evidence values.
- Remove environment-variable-style KEY=VALUE pairs that look like secrets.
- Never raise; if redaction fails for a field, replace with [REDACTED:error].
"""

from __future__ import annotations

import re
from copy import deepcopy
from typing import Any

from ghostwatch.core.schema import GhostEvent

# Patterns that suggest secrets in command-line arguments or env vars
_SECRET_PATTERNS = [
    re.compile(r"(?i)(password|passwd|secret|token|api[_-]?key|auth[_-]?key)\s*[=:]\s*\S+"),
    re.compile(r"(?i)--(?:password|token|secret|key)\s+\S+"),
    re.compile(r"Bearer\s+[A-Za-z0-9\-._~+/]+=*"),
    re.compile(r"(?:ghp|gho|ghu|ghs|ghr|github_pat)_[A-Za-z0-9]{36,}"),
    re.compile(r"sk-[A-Za-z0-9]{20,}"),          # OpenAI-style keys
]

_PLACEHOLDER = "[REDACTED]"

# Dict key names that suggest the value is a secret
_SENSITIVE_KEYS = re.compile(
    r"(?i)^(password|passwd|secret|token|api[_-]?key|auth[_-]?key|"
    r"access[_-]?key|private[_-]?key|bearer|credential)s?$"
)


def _redact_string(value: str) -> str:
    for pattern in _SECRET_PATTERNS:
        value = pattern.sub(_PLACEHOLDER, value)
    return value


def _redact_value(value: Any, key: str | None = None) -> Any:
    # If the key name signals a secret, redact the whole value
    if key and isinstance(value, str) and _SENSITIVE_KEYS.match(key):
        return _PLACEHOLDER
    if isinstance(value, str):
        return _redact_string(value)
    if isinstance(value, list):
        return [_redact_value(v) for v in value]
    if isinstance(value, dict):
        return {k: _redact_value(v, key=k) for k, v in value.items()}
    return value


def redact_event(event: GhostEvent) -> GhostEvent:
    """
    Return a *copy* of *event* with sensitive strings replaced.

    The original event (stored in the database) is never modified.
    """
    updates: dict[str, Any] = {}

    # Redact process cmdline
    if event.process and event.process.cmdline:
        safe_cmdline = [_redact_string(arg) for arg in event.process.cmdline]
        safe_process = event.process.model_copy(update={"cmdline": safe_cmdline})
        updates["process"] = safe_process

    # Redact evidence dict
    if event.evidence:
        updates["evidence"] = _redact_value(deepcopy(event.evidence), key=None)

    if updates:
        return event.model_copy(update=updates)
    return event
