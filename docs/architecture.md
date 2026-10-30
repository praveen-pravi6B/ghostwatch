# GhostWatch — Architecture

## Overview

GhostWatch is a local-first investigation tool. Every component runs on the user's machine. No telemetry, no cloud API calls, no remote model inference.

## Component diagram

```
┌─────────────────────────────────────────┐
│         Vue 3 + Vite dashboard          │
│         http://localhost:5173           │
└──────────────────┬──────────────────────┘
                   │ HTTP (localhost only)
┌──────────────────▼──────────────────────┐
│           FastAPI REST API              │
│           http://127.0.0.1:8765         │
│                                         │
│  /api/collect    → run collectors       │
│  /api/events     → list stored events   │
│  /api/investigate→ rules + AI pipeline  │
│  /api/status     → platform + AI health │
│  /api/events DELETE → clear local data  │
└──────┬───────────────────────┬──────────┘
       │                       │
┌──────▼──────┐    ┌───────────▼──────────┐
│  SQLite DB  │    │  Investigation core  │
│  (local     │    │                      │
│   file)     │    │  1. apply_rules()    │
└─────────────┘    │  2. redact_event()   │
                   │  3. OllamaClient     │
                   └───────────┬──────────┘
                               │ HTTP (localhost only)
                   ┌───────────▼──────────┐
                   │  Ollama / llama.cpp  │
                   │  http://127.0.0.1    │
                   │  :11434 or :8080     │
                   └──────────────────────┘

┌─────────────────────────────────────────┐
│          Platform adapters              │
│                                         │
│  macOS: log show --style=json           │
│  Linux: journalctl --output=json        │
│  Both:  psutil process snapshots        │
└─────────────────────────────────────────┘
```

## Data flow

```
Native OS telemetry
       ↓
Platform adapter (Linux/macOS)  +  psutil snapshots
       ↓
GhostEvent validation (Pydantic v2)
       ↓
SQLite storage (INSERT OR IGNORE deduplication)
       ↓
Deterministic rules (no AI involved)
       ↓
Redaction (strip tokens, passwords, API keys)
       ↓
Local model inference (Ollama, localhost only)
       ↓
Validated AIResponse (schema-enforced)
       ↓
Dashboard (facts and AI output displayed separately)
```

## Key design decisions

### Localhost binding
The FastAPI server binds to `127.0.0.1` only. CORS allows only localhost origins. The Ollama client validates that the configured URL is a localhost address before making any request.

### Rules before AI
Deterministic rules run first and produce `RuleFinding` objects that are stored with the event. The AI receives these findings as context but cannot override them. The dashboard displays rule findings and AI explanations in separate UI sections.

### Redaction boundary
`redact_event()` is called on a copy of each event before it is passed to the AI client. The original events stored in SQLite are never modified. The redaction covers command-line arguments and evidence dict values matching known secret patterns, plus any dict key whose name suggests a credential.

### Graceful degradation
- Ollama unavailable → events and rule findings still shown, AI panel shows offline notice
- journalctl missing → capability status set to UNAVAILABLE, no crash
- macOS privacy redactions → capability status set to PARTIAL, events still collected
- No root privileges → process fields that require elevation are set to None, noted in collection_note

### Platform isolation
`platforms/detect.py` uses deferred imports so Linux-only modules are never loaded on macOS and vice versa. The adapter interface (`LogAdapter`) is defined in `platforms/base.py`.
