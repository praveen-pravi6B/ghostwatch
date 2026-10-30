"""Abstract base for platform log adapters."""

from __future__ import annotations

from abc import ABC, abstractmethod

from ghostwatch.core.schema import CollectorCapability, GhostEvent


class LogAdapter(ABC):
    """
    Every platform adapter must implement this interface.

    collect() emits validated GhostEvent instances and a capability report.
    Missing telemetry should be reflected in AvailabilityStatus, not raised as an exception.
    """

    @abstractmethod
    async def collect(
        self,
        lookback_minutes: int = 60,
        max_events: int = 500,
    ) -> tuple[list[GhostEvent], CollectorCapability]:
        """
        Collect log events from the platform.

        Returns (events, capability) where capability describes what was accessible.
        """
