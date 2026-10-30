# GhostWatch

**Local-first AI investigation tool for unusual computer activity.**

GhostWatch collects process snapshots and OS log events, applies deterministic rules to identify interesting sequences, then asks a locally-running open-weight model to explain what the evidence shows — without sending a single byte to a cloud API.

> **Hacktoberfest 2026 — Ghost in the Machine challenge entry**

---

## What it does

1. **Collects** process snapshots (via `psutil`) and OS log events (`journalctl` on Linux, `log show` on macOS).
2. **Normalises** everything into a shared event schema and stores it in a local SQLite database.
3. **Applies rules** deterministically: temp-directory processes, interpreter download patterns, hidden process names, high-severity log entries.
4. **Redacts** sensitive fields (tokens, passwords, API keys) before any AI inference.
5. **Asks** a local Ollama model to explain the evidence, express uncertainty, and suggest manual follow-up steps.
6. **Displays** deterministic findings and AI explanations separately — facts stay facts.

GhostWatch is a **lightweight investigator**, not a guaranteed malware detector or a replacement for a full EDR system.

---

## Supported platforms

| Platform | Process snapshots | Log source |
|----------|-------------------|------------|
| macOS    | psutil            | `log show` (Unified Logging) |
| Linux (Ubuntu, Debian, Fedora, …) | psutil | `journalctl` (systemd) |

---

## Requirements

- Python 3.11+
- [Ollama](https://ollama.com) (optional — the app still collects and displays events without it)

---

## Quick start

```bash
# Clone and set up
git clone <repo>
cd ghostwatch
bash scripts/setup_dev.sh

# Run in sample mode (no privileges required, demo events loaded)
bash scripts/run_demo.sh

# Or run live (reads real OS logs where available)
.venv/bin/ghostwatch
```

The API binds to `127.0.0.1:8765` by default.

```bash
# Trigger a collection pass
curl -X POST http://127.0.0.1:8765/api/collect

# List collected events
curl http://127.0.0.1:8765/api/events

# Run an AI-assisted investigation
curl -X POST http://127.0.0.1:8765/api/investigate

# Check what's available
curl http://127.0.0.1:8765/api/status
```

---

## Configuration

All settings are environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `GHOSTWATCH_SAMPLE_MODE` | `false` | Load demo events instead of real telemetry |
| `GHOSTWATCH_OLLAMA_URL` | `http://127.0.0.1:11434` | Ollama endpoint (localhost only) |
| `GHOSTWATCH_MODEL` | `llama3.2` | Ollama model name |
| `GHOSTWATCH_DB` | `ghostwatch.db` | SQLite database path |
| `GHOSTWATCH_HOST` | `127.0.0.1` | API bind address |
| `GHOSTWATCH_PORT` | `8765` | API port |
| `GHOSTWATCH_LOG_LOOKBACK` | `60` | Minutes of OS logs to read |

---

## Running tests

```bash
.venv/bin/pytest tests/ -v
.venv/bin/ruff check ghostwatch/ tests/
```

---

## Privacy and safety

- The API binds to **localhost only** by default.
- No root or administrator privileges are required for core functionality.
- Log content is **never sent to a cloud API** — Ollama runs on your machine.
- Sensitive fields (tokens, passwords, API keys) are **redacted before AI inference**.
- AI-generated text is **never executed** as a shell command.
- Processes are **never terminated** automatically.
- Missing permissions and unavailable log sources are **reported as capability status**, not treated as application errors.

---

## Known limitations

- **Process snapshots use polling**: short-lived processes that start and exit between two snapshots will not be captured. This is inherent to the approach.
- **macOS Unified Logging** applies privacy redactions to some fields; these are noted in the capability status.
- **journalctl** requires systemd; non-systemd Linux distributions will show the journal as unavailable.
- GhostWatch does not perform kernel-level tracing, packet capture, or continuous background monitoring.

---

## Architecture

```
Astro + React dashboard (frontend/)
         |
     FastAPI API (ghostwatch/api/)
         |
  Investigation core (ghostwatch/core/)
  - schema, rules, redaction, investigator
         |
      SQLite (ghostwatch/storage/)
         |
  Platform adapters (ghostwatch/platforms/)
       /                \
    Linux              macOS
  journalctl        Unified Log
       \                /
     psutil snapshots (ghostwatch/collectors/)
         |
  Local Ollama HTTP API (localhost:11434)
```

See [docs/architecture.md](docs/architecture.md) for more detail.

---

## License

MIT
