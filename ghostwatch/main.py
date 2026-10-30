"""GhostWatch entry point."""

from __future__ import annotations

import logging

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from ghostwatch import config
from ghostwatch.ai.local_model import OllamaClient
from ghostwatch.api.routes import init as init_routes
from ghostwatch.api.routes import router
from ghostwatch.collectors.processes import ProcessSnapshotCollector
from ghostwatch.platforms.detect import get_log_adapter
from ghostwatch.storage.database import EventStore

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s — %(message)s",
)
log = logging.getLogger(__name__)

app = FastAPI(
    title="GhostWatch",
    description="Local-first AI investigation tool for unusual computer activity",
    version="0.1.0",
)

# CORS: only allow localhost origins so the API is not accessible cross-origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",   # Vite dev server
        "http://127.0.0.1:5173",
        "http://localhost:4173",   # Vite preview
        "http://127.0.0.1:4173",
    ],
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api")

store = EventStore(config.DB_PATH)
ollama = OllamaClient(config.OLLAMA_BASE_URL, config.OLLAMA_MODEL, config.OLLAMA_TIMEOUT)
process_collector = ProcessSnapshotCollector()
log_adapter = get_log_adapter()

init_routes(store, ollama, process_collector, log_adapter, config.SAMPLE_MODE)


@app.on_event("startup")
async def on_startup() -> None:
    await store.open()
    platform_name = "sample mode" if config.SAMPLE_MODE else (
        log_adapter.__class__.__name__ if log_adapter else "no log adapter"
    )
    log.info("GhostWatch started — platform adapter: %s", platform_name)
    if not await ollama.is_available():
        log.warning(
            "Ollama not reachable at %s — event collection and rules still work; "
            "AI explanations will be unavailable until Ollama is running.",
            config.OLLAMA_BASE_URL,
        )


@app.on_event("shutdown")
async def on_shutdown() -> None:
    await store.close()


def cli() -> None:
    uvicorn.run(
        "ghostwatch.main:app",
        host=config.API_HOST,
        port=config.API_PORT,
        reload=False,
    )


if __name__ == "__main__":
    cli()
