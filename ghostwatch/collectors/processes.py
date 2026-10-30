"""Process snapshot collector using psutil.

Compares the current snapshot against the previous one and emits GhostEvent
instances for newly observed processes. Short-lived processes can be missed
between snapshots — this is documented, not papered over.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime

import psutil

from ghostwatch.core.schema import (
    AvailabilityStatus,
    CollectorCapability,
    EventSource,
    GhostEvent,
    ProcessInfo,
    Severity,
)

log = logging.getLogger(__name__)


def _safe_proc_info(proc: psutil.Process) -> ProcessInfo:
    """Extract process fields defensively; use None for inaccessible values."""
    try:
        name = proc.name()
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        name = None
    try:
        exe = proc.exe()
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        exe = None
    try:
        cmdline = proc.cmdline()
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        cmdline = None
    try:
        create_time = datetime.fromtimestamp(proc.create_time(), tz=UTC)
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        create_time = None
    try:
        username = proc.username()
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        username = None
    try:
        ppid = proc.ppid()
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        ppid = None

    return ProcessInfo(
        pid=proc.pid,
        ppid=ppid,
        name=name,
        exe=exe,
        cmdline=cmdline,
        create_time=create_time,
        username=username,
    )


class ProcessSnapshotCollector:
    """
    Maintains a set of previously-seen PIDs and emits events for new ones.

    Known limitation: processes that start and exit between two snapshots will
    not be captured. This is inherent to the polling approach and is documented
    clearly rather than hidden.
    """

    def __init__(self) -> None:
        self._seen_pids: set[int] = set()

    def snapshot(self) -> tuple[list[GhostEvent], CollectorCapability]:
        """
        Take a process snapshot and return events for new processes.

        First call returns all currently running processes as events.
        Subsequent calls return only newly started processes.
        """
        try:
            current: dict[int, psutil.Process] = {
                p.pid: p for p in psutil.process_iter(["pid"])
            }
        except Exception as exc:
            return [], CollectorCapability(
                name="process_snapshot",
                status=AvailabilityStatus.UNAVAILABLE,
                note=f"psutil failed: {exc}",
            )

        new_pids = set(current.keys()) - self._seen_pids
        self._seen_pids = set(current.keys())

        events: list[GhostEvent] = []
        access_denied_count = 0

        for pid in new_pids:
            proc = current.get(pid)
            if proc is None:
                continue  # exited already
            try:
                info = _safe_proc_info(proc)
                if info.exe is None and info.name is None:
                    access_denied_count += 1

                event = GhostEvent(
                    timestamp=info.create_time or datetime.now(tz=UTC),
                    source=EventSource.PROCESS_SNAPSHOT,
                    event_type="process_new",
                    summary=f"New process observed: {info.name or '[unknown]'} (PID {pid})",
                    severity=Severity.INFO,
                    process=info,
                    evidence={"pid": pid},
                    availability=AvailabilityStatus.OK
                    if info.exe is not None
                    else AvailabilityStatus.PARTIAL,
                    collection_note=(
                        "Some process fields inaccessible without elevated privileges."
                        if info.exe is None
                        else None
                    ),
                )
                events.append(event)
            except Exception:
                log.debug("Could not create event for PID %d", pid, exc_info=True)

        note = f"Snapshot: {len(events)} new process(es) observed."
        if access_denied_count:
            note += f" {access_denied_count} had restricted fields (no elevated privileges)."

        return events, CollectorCapability(
            name="process_snapshot",
            status=AvailabilityStatus.OK,
            note=note,
        )
