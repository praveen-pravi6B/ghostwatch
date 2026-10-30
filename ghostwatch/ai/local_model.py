"""Client for a local inference server (llama.cpp or Ollama).

Uses the OpenAI-compatible /v1/chat/completions endpoint, which both
llama.cpp server and Ollama expose. Point GHOSTWATCH_OLLAMA_URL at
whichever is running:

  llama.cpp default:  http://127.0.0.1:8080
  Ollama default:     http://127.0.0.1:11434

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


class AIUnavailableError(RuntimeError):
    """Raised when the local inference server is not reachable."""


# Keep the old name as an alias so existing code that catches it still works
OllamaUnavailableError = AIUnavailableError


class AIResponse(BaseModel):
    explanation: str
    evidence_references: list[str] = []
    uncertainty: str
    next_steps: list[str] = []

    model_config = {"extra": "ignore"}


# Health-check paths tried in order (llama.cpp first, then Ollama)
_HEALTH_PATHS = ["/health", "/api/tags"]


class OllamaClient:
    """
    Inference client compatible with llama.cpp server and Ollama.

    Both expose POST /v1/chat/completions (OpenAI-compatible).
    llama.cpp default port: 8080  |  Ollama default port: 11434
    """

    def __init__(self, base_url: str, model: str, timeout: float = 120.0) -> None:
        if not base_url.startswith(("http://127.0.0.1", "http://localhost")):
            raise ValueError(
                f"AI base_url must be a localhost address, got: {base_url!r}. "
                "GhostWatch never connects to remote AI endpoints."
            )
        self._base_url = base_url.rstrip("/")
        self._model = model
        self._timeout = timeout

    async def is_available(self) -> bool:
        """
        Health check — tries /health (llama.cpp) then /api/tags (Ollama).
        Does not send any log data.
        """
        async with httpx.AsyncClient(timeout=5) as client:
            for path in _HEALTH_PATHS:
                try:
                    resp = await client.get(f"{self._base_url}{path}")
                    if resp.status_code == 200:
                        return True
                except Exception:
                    continue
        return False

    async def explain_events(self, events: list[GhostEvent]) -> dict:
        """
        Send redacted events to the local model via /v1/chat/completions.

        Raises AIUnavailableError if the server cannot be reached.
        Returns an empty dict if the model response is malformed.
        """
        if not events:
            return {}

        user_message = build_user_message(events)

        # OpenAI-compatible payload — works with both llama.cpp and Ollama
        payload = {
            "model": self._model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_message},
            ],
            "stream": False,
            "temperature": 0.1,
            "response_format": {"type": "json_object"},
        }

        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                resp = await client.post(
                    f"{self._base_url}/v1/chat/completions",
                    json=payload,
                )
                resp.raise_for_status()
        except httpx.ConnectError as exc:
            raise AIUnavailableError(
                f"Cannot connect to local AI server at {self._base_url}. "
                "Start llama.cpp server: `llama-server -m model.gguf` "
                "or Ollama: `ollama serve`"
            ) from exc
        except httpx.HTTPStatusError as exc:
            raise AIUnavailableError(
                f"AI server returned HTTP {exc.response.status_code}"
            ) from exc
        except httpx.TimeoutException as exc:
            raise AIUnavailableError("AI request timed out.") from exc

        try:
            raw_content = resp.json()["choices"][0]["message"]["content"]
        except (KeyError, IndexError, json.JSONDecodeError) as exc:
            log.warning("Unexpected AI response structure: %s", exc)
            return {}

        # Parse and validate the model's JSON output
        try:
            parsed = json.loads(raw_content) if isinstance(raw_content, str) else raw_content
            validated = AIResponse.model_validate(parsed)
            return validated.model_dump()
        except (json.JSONDecodeError, ValidationError) as exc:
            log.warning("Model returned invalid response structure: %s", exc)
            try:
                partial = json.loads(raw_content) if isinstance(raw_content, str) else raw_content
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
