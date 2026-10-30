"""FastAPI routes for the GhostWatch API."""

from __future__ import annotations

import json
import logging
from pathlib import Path

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from ghostwatch.core.investigator import Investigation, investigate
from ghostwatch.core.rules import apply_rules
from ghostwatch.core.schema import GhostEvent

log = logging.getLogger(__name__)
router = APIRouter()

# These are injected by main.py at startup
_store = None
_ollama = None
_process_collector = None
_log_adapter = None
_sample_mode = False


def init(store, ollama, process_collector, log_adapter, sample_mode: bool = False) -> None:
    global _store, _ollama, _process_collector, _log_adapter, _sample_mode
    _store = store
    _ollama = ollama
    _process_collector = process_collector
    _log_adapter = log_adapter
    _sample_mode = sample_mode


class StatusResponse(BaseModel):
    platform: str
    ollama_available: bool
    ollama_model: str
    sample_mode: bool
    capabilities: list[dict]


class InvestigationResponse(BaseModel):
    events: list[dict]
    rule_summary: list[str]
    ai_explanation: str | None
    ai_evidence_refs: list[str]
    ai_uncertainty: str | None
    ai_next_steps: list[str]
    ai_available: bool
    ai_error: str | None


@router.get("/status", response_model=StatusResponse)
async def get_status():
    from ghostwatch import config
    from ghostwatch.platforms.detect import current_platform

    ollama_available = await _ollama.is_available() if _ollama else False
    return StatusResponse(
        platform=current_platform(),
        ollama_available=ollama_available,
        ollama_model=config.OLLAMA_MODEL,
        sample_mode=_sample_mode,
        capabilities=[],
    )


@router.get("/events")
async def list_events(limit: int = Query(200, le=1000)):
    events = await _store.list_events(limit=limit)
    return [json.loads(e.model_dump_json()) for e in events]


@router.post("/collect")
async def run_collection():
    """Trigger a manual collection pass."""
    capabilities: list[dict] = []
    events_saved = 0

    if _sample_mode:
        sample_path = Path(__file__).parent.parent.parent / "tests/fixtures/sample_events.json"
        raw = json.loads(sample_path.read_text())
        for item in raw:
            ev = GhostEvent.model_validate(item)
            ev = apply_rules(ev)
            saved = await _store.save_event(ev)
            if saved:
                events_saved += 1
        capabilities.append({"name": "sample_data", "status": "ok", "note": "Loaded sample events."})
    else:
        # Process snapshots
        if _process_collector:
            proc_events, proc_cap = _process_collector.snapshot()
            capabilities.append(proc_cap.model_dump())
            for ev in proc_events:
                ev = apply_rules(ev)
                saved = await _store.save_event(ev)
                if saved:
                    events_saved += 1

        # Platform log adapter
        if _log_adapter:
            try:
                log_events, log_cap = await _log_adapter.collect()
                capabilities.append(log_cap.model_dump())
                for ev in log_events:
                    ev = apply_rules(ev)
                    saved = await _store.save_event(ev)
                    if saved:
                        events_saved += 1
            except Exception as exc:
                log.warning("Log adapter error: %s", exc)
                capabilities.append({
                    "name": "log_adapter",
                    "status": "unavailable",
                    "note": str(exc),
                })

    return {"events_saved": events_saved, "capabilities": capabilities}


@router.post("/investigate", response_model=InvestigationResponse)
async def run_investigation(limit: int = Query(50, le=200)):
    events = await _store.list_events(limit=limit)
    if not events:
        raise HTTPException(status_code=404, detail="No events to investigate. Run /collect first.")
    result: Investigation = await investigate(events, _ollama)
    return InvestigationResponse(
        events=[json.loads(e.model_dump_json()) for e in result.events],
        rule_summary=result.rule_summary,
        ai_explanation=result.ai_explanation,
        ai_evidence_refs=result.ai_evidence_refs,
        ai_uncertainty=result.ai_uncertainty,
        ai_next_steps=result.ai_next_steps,
        ai_available=result.ai_available,
        ai_error=result.ai_error,
    )


@router.delete("/events")
async def clear_events():
    """Delete all stored events."""
    count = await _store.clear()
    return {"deleted": count}
