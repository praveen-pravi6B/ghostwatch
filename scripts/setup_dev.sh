#!/usr/bin/env bash
# GhostWatch development setup
set -euo pipefail

echo "==> Checking Python 3.11+"
python3 --version

echo "==> Creating virtual environment"
python3 -m venv .venv

echo "==> Installing GhostWatch + dev dependencies"
.venv/bin/pip install -e ".[dev]" -q

echo "==> Checking Ollama"
if command -v ollama &>/dev/null; then
    echo "    Ollama found: $(ollama --version 2>&1 | head -1)"
    echo "    If not already running: ollama serve"
    echo "    Pull a model:           ollama pull llama3.2"
else
    echo "    Ollama not found. Install from https://ollama.com"
    echo "    GhostWatch works without Ollama; AI explanations will be unavailable."
fi

echo ""
echo "Setup complete."
echo ""
echo "To start the API:"
echo "  .venv/bin/ghostwatch"
echo ""
echo "To run in sample mode (no privileges needed):"
echo "  GHOSTWATCH_SAMPLE_MODE=true .venv/bin/ghostwatch"
echo ""
echo "To run tests:"
echo "  .venv/bin/pytest tests/ -v"
