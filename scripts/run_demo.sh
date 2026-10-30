#!/usr/bin/env bash
# Run GhostWatch in sample mode — no special permissions required
set -euo pipefail

export GHOSTWATCH_SAMPLE_MODE=true
export GHOSTWATCH_DB=ghostwatch_demo.db

echo "==> Starting GhostWatch in SAMPLE MODE"
echo ""
echo "    API:       http://127.0.0.1:8765/api"
echo "    Dashboard: http://localhost:5173  (open this in your browser)"
echo ""
echo "    Press Ctrl-C to stop."
echo ""

# Start API in background
.venv/bin/ghostwatch &
API_PID=$!

# Start Vue dev server
cd frontend && npm run dev &
UI_PID=$!

# Wait for either to exit
wait $API_PID $UI_PID
