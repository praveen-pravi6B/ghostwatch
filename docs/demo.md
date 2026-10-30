# GhostWatch — Demo Guide

This guide walks through the sample-data demo. No root privileges, no real suspicious activity, and no Ollama required for the event/rules view.

## Prerequisites

- Python 3.11+
- Node.js 18+
- (Optional) Ollama with `llama3.2` or `qwen2.5:1.5b` for AI explanations

## Setup

```bash
git clone <repo>
cd ghostwatch
bash scripts/setup_dev.sh
```

## Run the demo

### Terminal 1 — API (sample mode)
```bash
GHOSTWATCH_SAMPLE_MODE=true .venv/bin/ghostwatch
```

### Terminal 2 — Dashboard
```bash
cd frontend && npm run dev
# opens at http://localhost:5173
```

## What you'll see

Open **http://localhost:5173** in your browser.

### Step 1 — Collect
Click **⚡ Collect**. Four pre-built sample events load:

| Event | What it simulates |
|-------|------------------|
| `python3` from `/tmp` | Script launched from a temp directory with a network URL in args |
| `sudo /bin/bash` from `/tmp` | Privilege escalation from a temp directory |
| `.hidden_daemon` from `/var/tmp` | Process with a hidden name running from a temp directory |
| iptables policy change | Firewall rule change logged by the kernel |

### Step 2 — Review the timeline
The activity timeline shows each event with:
- Severity badge (notice / warning)
- Source (journal / process_snapshot)
- Timestamp
- Process details (PID, exe path, user)
- Rule findings highlighted in amber

Three rules fire on these events:
- **PROC_TEMP_DIR** — process launched from `/tmp` or `/var/tmp`
- **PROC_HIDDEN_NAME** — process name starts with a dot
- **INTERP_NETWORK_CMDLINE** — Python process with `https://` in command line

### Step 3 — Investigate
Click **🔍 Investigate**. If Ollama is running, the right panel fills with:
- Rule findings list
- AI explanation (plain language, evidence-referenced)
- Uncertainty disclosure
- Suggested manual checks

If Ollama is offline, rule findings still display — the AI panel shows an offline notice.

### Step 4 — Clear
Click **🗑 Clear** to reset and run again.

## With Ollama

```bash
# Install Ollama from https://ollama.com
ollama pull qwen2.5:1.5b          # fast on CPU
GHOSTWATCH_MODEL=qwen2.5:1.5b GHOSTWATCH_SAMPLE_MODE=true .venv/bin/ghostwatch
```

## Live collection (no sample mode)

Remove `GHOSTWATCH_SAMPLE_MODE=true` to collect real process snapshots and OS logs:

```bash
.venv/bin/ghostwatch
# macOS: reads Unified Log via `log show`
# Linux: reads systemd journal via `journalctl`
```

Some fields require elevated privileges. GhostWatch notes what it cannot access rather than failing.
