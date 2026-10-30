"""Linux platform adapter — reads from journalctl in JSON mode."""

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


def _map_priority(priority: int | str | None) -> Severity:
    """Map syslog priority (0-7) to Severity."""
    try:
        p = int(priority or 6)
    except (ValueError, TypeError):
        return Severity.INFO
    if p <= 2:
        return Severity.HIGH
    if p == 3:
        return Severity.WARNING
    if p == 4:
        return Severity.NOTICE
    return Severity.INFO


class JournalAdapter(LogAdapter):
    """
    Reads bounded journalctl output in JSON mode.

    Requires systemd. Falls back gracefully when:
    - journalctl is not installed
    - the calling user has no access to the journal
    - the system does not use systemd
    """

    async def collect(
        self,
        lookback_minutes: int = 60,
        max_events: int = 500,
    ) -> tuple[list[GhostEvent], CollectorCapability]:
        if not shutil.which("journalctl"):
            return [], CollectorCapability(
                name="journalctl",
                status=AvailabilityStatus.UNAVAILABLE,
                note="journalctl not found; system may not use systemd.",
            )

        since_dt = datetime.now(tz=UTC) - timedelta(minutes=lookback_minutes)
        since_str = since_dt.strftime("%Y-%m-%d %H:%M:%S")

        cmd = [
            "journalctl",
            "--output=json",
            f"--since={since_str}",
            f"--lines={max_events}",
            "--no-pager",
        ]

        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=30)
        except TimeoutError:
            return [], CollectorCapability(
                name="journalctl",
                status=AvailabilityStatus.PARTIAL,
                note="journalctl timed out after 30 s.",
            )
        except Exception as exc:
            return [], CollectorCapability(
                name="journalctl",
                status=AvailabilityStatus.UNAVAILABLE,
                note=f"journalctl execution failed: {exc}",
            )

        err_text = stderr.decode(errors="replace").strip()

        # returncode 0 = success, 1 = no entries OR error (distinguish by stderr)
        if proc.returncode not in (0, 1) or (proc.returncode == 1 and err_text):
            if "permission" in err_text.lower() or "access" in err_text.lower():
                status = AvailabilityStatus.PERMISSION_DENIED
            else:
                status = AvailabilityStatus.UNAVAILABLE
            return [], CollectorCapability(
                name="journalctl",
                status=status,
                note=err_text[:300] or "journalctl returned non-zero exit code.",
            )

        events: list[GhostEvent] = []
        for line in stdout.decode(errors="replace").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue

            raw_ts = entry.get("__REALTIME_TIMESTAMP")
            if raw_ts:
                ts = datetime.fromtimestamp(int(raw_ts) / 1_000_000, tz=UTC)
            else:
                ts = datetime.now(tz=UTC)

            message = entry.get("MESSAGE", "")
            if not message:
                continue

            pid = entry.get("_PID")
            process = ProcessInfo(
                pid=int(pid) if pid else None,
                name=entry.get("_COMM"),
                exe=entry.get("_EXE"),
                username=entry.get("_UID"),
            )

            severity = _map_priority(entry.get("PRIORITY"))

            try:
                event = GhostEvent(
                    timestamp=ts,
                    source=EventSource.JOURNAL,
                    event_type=f"journal.{entry.get('SYSLOG_IDENTIFIER', 'unknown')}",
                    summary=str(message)[:500],
                    severity=severity,
                    process=process,
                    evidence={
                        "unit": entry.get("_SYSTEMD_UNIT"),
                        "transport": entry.get("_TRANSPORT"),
                        "hostname": entry.get("_HOSTNAME"),
                    },
                    availability=AvailabilityStatus.OK,
                )
                events.append(event)
            except Exception:
                log.debug("Skipping unparseable journal entry", exc_info=True)

        return events, CollectorCapability(
            name="journalctl",
            status=AvailabilityStatus.OK,
            note=f"Collected {len(events)} journal entries.",
        )
