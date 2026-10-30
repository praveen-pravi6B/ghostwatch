#!/usr/bin/env bash
# Run GhostWatch in sample mode — no special permissions required
set -euo pipefail

export GHOSTWATCH_SAMPLE_MODE=true
export GHOSTWATCH_DB=ghostwatch_demo.db

echo "==> Starting GhostWatch in SAMPLE MODE"
echo "    API: http://127.0.0.1:8765"
echo "    Collect: POST http://127.0.0.1:8765/api/collect"
echo "    Events:  GET  http://127.0.0.1:8765/api/events"
echo "    Investigate: POST http://127.0.0.1:8765/api/investigate"
echo ""
echo "    Press Ctrl-C to stop."
echo ""

.venv/bin/ghostwatch
