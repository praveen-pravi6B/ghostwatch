"""Orchestrates the investigation pipeline for a set of events."""

from __future__ import annotations

from dataclasses import dataclass, field

from ghostwatch.ai.local_model import OllamaClient, OllamaUnavailableError
from ghostwatch.core.redact import redact_event
from ghostwatch.core.rules import apply_rules
from ghostwatch.core.schema import GhostEvent


@dataclass
class Investigation:
    events: list[GhostEvent] = field(default_factory=list)
    rule_summary: list[str] = field(default_factory=list)
    ai_explanation: str | None = None
    ai_evidence_refs: list[str] = field(default_factory=list)
    ai_uncertainty: str | None = None
    ai_next_steps: list[str] = field(default_factory=list)
    ai_available: bool = True
    ai_error: str | None = None


async def investigate(events: list[GhostEvent], client: OllamaClient) -> Investigation:
    """
    Run deterministic rules on *events*, then ask the local model to explain findings.

    The AI is given only redacted events. Findings from deterministic rules are stored
    independently and displayed alongside (not overridden by) the AI response.
    """
    # 1. Apply deterministic rules
    ruled_events = [apply_rules(e) for e in events]

    # 2. Collect rule summaries for display
    rule_summaries: list[str] = []
    for ev in ruled_events:
        for f in ev.rule_findings:
            rule_summaries.append(f"[{f.rule_id}] {f.description}")

    # 3. Redact before AI
    redacted = [redact_event(e) for e in ruled_events]

    # 4. Ask the model
    ai_result: dict = {}
    ai_available = True
    ai_error: str | None = None

    try:
        ai_result = await client.explain_events(redacted)
    except OllamaUnavailableError as exc:
        ai_available = False
        ai_error = str(exc)
    except Exception as exc:  # noqa: BLE001
        ai_available = False
        ai_error = f"Unexpected AI error: {exc}"

    return Investigation(
        events=ruled_events,
        rule_summary=rule_summaries,
        ai_explanation=ai_result.get("explanation"),
        ai_evidence_refs=ai_result.get("evidence_references", []),
        ai_uncertainty=ai_result.get("uncertainty"),
        ai_next_steps=ai_result.get("next_steps", []),
        ai_available=ai_available,
        ai_error=ai_error,
    )
