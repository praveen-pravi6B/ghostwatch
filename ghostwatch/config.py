"""GhostWatch configuration — all knobs in one place."""

from __future__ import annotations

import os
from pathlib import Path

# --- Ollama ---
OLLAMA_BASE_URL: str = os.environ.get("GHOSTWATCH_OLLAMA_URL", "http://127.0.0.1:11434")
OLLAMA_MODEL: str = os.environ.get("GHOSTWATCH_MODEL", "llama3.2")
OLLAMA_TIMEOUT: float = float(os.environ.get("GHOSTWATCH_OLLAMA_TIMEOUT", "60"))

# --- Storage ---
DB_PATH: Path = Path(os.environ.get("GHOSTWATCH_DB", "ghostwatch.db"))

# --- Collection ---
SNAPSHOT_INTERVAL_SECONDS: int = int(os.environ.get("GHOSTWATCH_SNAPSHOT_INTERVAL", "30"))
LOG_LOOKBACK_MINUTES: int = int(os.environ.get("GHOSTWATCH_LOG_LOOKBACK", "60"))
MAX_LOG_EVENTS: int = int(os.environ.get("GHOSTWATCH_MAX_LOG_EVENTS", "500"))

# --- API ---
API_HOST: str = os.environ.get("GHOSTWATCH_HOST", "127.0.0.1")  # localhost-only by default
API_PORT: int = int(os.environ.get("GHOSTWATCH_PORT", "8765"))

# --- Modes ---
SAMPLE_MODE: bool = os.environ.get("GHOSTWATCH_SAMPLE_MODE", "").lower() in ("1", "true", "yes")
