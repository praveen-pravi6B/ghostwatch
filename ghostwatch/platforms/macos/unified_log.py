"""macOS platform adapter — reads from the Unified Logging system via `log` utility."""

from __future__ import annotations

import asyncio
import json
import logging
import shutil
from datetime import UTC, datetime, timedelta

from ghostwatch.core.schema import (
    AvailabilityStatus,
    CollectorCapability,
    EventSource,
    GhostEvent,
    ProcessInfo,
    Severity,
)
from ghostwatch.platforms.base import LogAdapter

log = logging.getLogger(__name__)

_LOG_TYPE_TO_SEVERITY = {
    "fault": Severity.HIGH,
    "error": Severity.WARNING,
    "debug": Severity.INFO,
    "info": Severity.INFO,
    "default": Severity.INFO,
}


class UnifiedLogAdapter(LogAdapter):
    """
    Reads bounded Unified Logging entries using the macOS `log` utility.

    Falls back gracefully when:
    - `log` is not available (non-macOS or sandboxed environment)
    - Privacy redactions limit content (noted, not treated as an error)
    - The command times out
    """

    async def collect(
        self,
        lookback_minutes: int = 60,
        max_events: int = 500,
    ) -> tuple[list[GhostEvent], CollectorCapability]:
        if not shutil.which("log"):
            return [], CollectorCapability(
                name="unified_log",
                status=AvailabilityStatus.UNAVAILABLE,
                note="`log` utility not found; not running on macOS.",
            )

        since_dt = datetime.now(tz=UTC) - timedelta(minutes=lookback_minutes)
        since_str = since_dt.strftime("%Y-%m-%d %H:%M:%S")

        cmd = [
            "log",
            "show",
            "--style=json",
            f"--start={since_str}",
            "--last",
            f"{lookback_minutes}m",
        ]

        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=60)
        except TimeoutError:
            return [], CollectorCapability(
                name="unified_log",
                status=AvailabilityStatus.PARTIAL,
                note="`log show` timed out after 60 s.",
            )
        except Exception as exc:
            return [], CollectorCapability(
                name="unified_log",
                status=AvailabilityStatus.UNAVAILABLE,
                note=f"`log` execution failed: {exc}",
            )

        if proc.returncode != 0:
            err_text = stderr.decode(errors="replace").strip()
            return [], CollectorCapability(
                name="unified_log",
                status=AvailabilityStatus.UNAVAILABLE,
                note=err_text[:300] or "`log show` returned non-zero exit.",
            )

        raw = stdout.decode(errors="replace").strip()
        # The `log show --style=json` output is a JSON array
        try:
            entries: list[dict] = json.loads(raw)
        except json.JSONDecodeError:
            return [], CollectorCapability(
                name="unified_log",
                status=AvailabilityStatus.PARTIAL,
                note="Could not parse JSON from `log show`. Output may be empty or malformed.",
            )

        events: list[GhostEvent] = []
        privacy_redacted = 0

        for entry in entries[:max_events]:
            message = entry.get("eventMessage", "")
            if not message:
                continue

            # Track privacy redactions but don't drop the event
            if "<private>" in message:
                privacy_redacted += 1

            ts_str = entry.get("timestamp")
            try:
                ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00")) if ts_str else datetime.now(tz=UTC)
            except Exception:
                ts = datetime.now(tz=UTC)

            log_type = entry.get("messageType", "default").lower()
            severity = _LOG_TYPE_TO_SEVERITY.get(log_type, Severity.INFO)

            process = ProcessInfo(
                pid=entry.get("processID"),
                name=entry.get("process"),
                exe=entry.get("senderImagePath"),
            )

            try:
                event = GhostEvent(
                    timestamp=ts,
                    source=EventSource.UNIFIED_LOG,
                    event_type=f"unified_log.{log_type}",
                    summary=str(message)[:500],
                    severity=severity,
                    process=process,
                    evidence={
                        "subsystem": entry.get("subsystem"),
                        "category": entry.get("category"),
                        "sender": entry.get("sender"),
                    },
                    availability=AvailabilityStatus.OK,
                )
                events.append(event)
            except Exception:
                log.debug("Skipping unparseable unified log entry", exc_info=True)

        note = f"Collected {len(events)} entries."
        status = AvailabilityStatus.OK
        if privacy_redacted:
            note += f" {privacy_redacted} entries contained <private> redactions (macOS privacy policy)."
            status = AvailabilityStatus.PARTIAL

        return events, CollectorCapability(name="unified_log", status=status, note=note)
