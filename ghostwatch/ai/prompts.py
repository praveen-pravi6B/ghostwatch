"""Prompt templates for local model inference.

Log content is treated as untrusted data and injected into a structured
section, not interpolated into the instruction text.
"""

from __future__ import annotations

import json

from ghostwatch.core.schema import GhostEvent

SYSTEM_PROMPT = """\
You are an assistant helping investigate unusual computer activity.
You will receive a list of system events as structured JSON.
Your job is to explain what the evidence shows, what is uncertain, and what a user could check manually.

Rules you must follow:
- Only reference facts present in the supplied evidence. Do not invent details.
- Do not declare the system "compromised" or "infected" — say what the evidence suggests.
- Disclose your uncertainty clearly.
- Do not suggest executing any shell commands yourself.
- Return ONLY valid JSON matching the schema below — no prose outside the JSON.

Response schema:
{
  "explanation": "<plain-language explanation of the events, max 400 words>",
  "evidence_references": ["<event id or field that supports the explanation>", ...],
  "uncertainty": "<what is not known or cannot be concluded from this evidence>",
  "next_steps": ["<manual check the user could perform>", ...]
}
"""


def build_user_message(events: list[GhostEvent]) -> str:
    """Serialize redacted events into the user turn of the prompt.

    Only include fields the model needs — keeps the prompt short for fast local inference.
    """
    payload = []
    for ev in events:
        entry: dict = {
            "id": ev.id,
            "time": ev.timestamp.strftime("%H:%M:%S"),
            "source": ev.source.value,
            "type": ev.event_type,
            "summary": ev.summary,
            "severity": ev.severity.value,
        }
        if ev.process:
            p = ev.process
            entry["process"] = {k: v for k, v in {
                "pid": p.pid, "name": p.name, "exe": p.exe,
                "cmdline": " ".join(p.cmdline) if p.cmdline else None,
                "user": p.username,
            }.items() if v is not None}
        if ev.rule_findings:
            entry["rule_flags"] = [f.rule_id for f in ev.rule_findings]
        payload.append(entry)

    return (
        "Investigate the following system events and return the JSON response:\n\n"
        "```json\n"
        + json.dumps(payload, default=str, indent=2)
        + "\n```"
    )
