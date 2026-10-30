"""Client for the local Ollama HTTP API.

Connects to localhost only. Never falls back to a cloud endpoint.
Validates model output against the expected schema.
"""

from __future__ import annotations

import json
import logging

import httpx
from pydantic import BaseModel, ValidationError

from ghostwatch.ai.prompts import SYSTEM_PROMPT, build_user_message
from ghostwatch.core.schema import GhostEvent

log = logging.getLogger(__name__)


class OllamaUnavailableError(RuntimeError):
    """Raised when Ollama is not reachable or returns an unexpected error."""


class AIResponse(BaseModel):
    explanation: str
    evidence_references: list[str] = []
    uncertainty: str
    next_steps: list[str] = []

    model_config = {"extra": "ignore"}


class OllamaClient:
    def __init__(self, base_url: str, model: str, timeout: float = 60.0) -> None:
        if not base_url.startswith(("http://127.0.0.1", "http://localhost")):
            raise ValueError(
                f"Ollama base_url must be a localhost address, got: {base_url!r}. "
                "GhostWatch never connects to remote AI endpoints."
            )
        self._base_url = base_url.rstrip("/")
        self._model = model
        self._timeout = timeout

    async def is_available(self) -> bool:
        """Quick health check — does not send any log data."""
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                resp = await client.get(f"{self._base_url}/api/tags")
                return resp.status_code == 200
        except Exception:
            return False

    async def explain_events(self, events: list[GhostEvent]) -> dict:
        """
        Send redacted events to the local model and return validated AI response.

        Raises OllamaUnavailableError if Ollama cannot be reached.
        Returns an empty dict if the model response is malformed.
        """
        if not events:
            return {}

        user_message = build_user_message(events)
        payload = {
            "model": self._model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_message},
            ],
            "stream": False,
            "format": "json",
            "options": {"temperature": 0.1},
        }

        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                resp = await client.post(
                    f"{self._base_url}/api/chat",
                    json=payload,
                )
                resp.raise_for_status()
        except httpx.ConnectError as exc:
            raise OllamaUnavailableError(
                f"Cannot connect to Ollama at {self._base_url}. "
                "Make sure Ollama is running: `ollama serve`"
            ) from exc
        except httpx.HTTPStatusError as exc:
            raise OllamaUnavailableError(
                f"Ollama returned HTTP {exc.response.status_code}"
            ) from exc
        except httpx.TimeoutException as exc:
            raise OllamaUnavailableError("Ollama request timed out.") from exc

        try:
            raw_content = resp.json()["message"]["content"]
        except (KeyError, json.JSONDecodeError) as exc:
            log.warning("Unexpected Ollama response structure: %s", exc)
            return {}

        # Parse and validate the model's JSON output
        try:
            parsed = json.loads(raw_content)
            validated = AIResponse.model_validate(parsed)
            return validated.model_dump()
        except (json.JSONDecodeError, ValidationError) as exc:
            log.warning("Model returned invalid response structure: %s", exc)
            # Return partial data if explanation is at least present
            try:
                partial = json.loads(raw_content)
                if isinstance(partial, dict) and "explanation" in partial:
                    return {
                        "explanation": str(partial["explanation"])[:1000],
                        "evidence_references": [],
                        "uncertainty": "Model response did not fully conform to schema.",
                        "next_steps": [],
                    }
            except Exception:
                pass
            return {}
