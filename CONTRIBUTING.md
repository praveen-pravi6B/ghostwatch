# Contributing to GhostWatch

Thank you for your interest in contributing! GhostWatch is a local-first, open-source AI investigation tool for unusual computer activity. This guide covers how to set up the project, submit changes, and stay aligned with the project's core design constraints.

---

## Table of Contents

- [Project Setup](#project-setup)
- [Branch and PR Workflow](#branch-and-pr-workflow)
- [Code Style](#code-style)
- [Testing Requirements](#testing-requirements)
- [Project Structure](#project-structure)
- [Non-Negotiable Constraints](#non-negotiable-constraints)
- [Getting Help](#getting-help)

---

## Project Setup

### Prerequisites

- **Python** ≥ 3.11
- **Node.js** ≥ 18
- **Git**
- **Ollama** (optional — for AI explanation features)

### Install and build

```bash
git clone https://github.com/praveen-pravi6B/ghostwatch.git
cd ghostwatch

# Create virtual environment and install dependencies
python3 -m venv .venv
.venv/bin/pip install -e ".[dev]"

# Install frontend dependencies
cd frontend && npm install && cd ..

# Verify the test suite passes
.venv/bin/pytest tests/ -v

# Verify linting passes
.venv/bin/ruff check ghostwatch/ tests/
```

### Run in sample mode (no privileges required)

```bash
# Terminal 1 — API
GHOSTWATCH_SAMPLE_MODE=true .venv/bin/ghostwatch

# Terminal 2 — Dashboard
cd frontend && npm run dev
# Open http://localhost:5173
```

---

## Branch and PR Workflow

1. **Fork** the repository and create a branch from `main`:
   ```bash
   git checkout -b feat/your-feature-name
   # or
   git checkout -b fix/your-bug-description
   ```

2. **Make your changes.** Keep commits focused — one logical change per commit.

3. **Run tests and linting before pushing:**
   ```bash
   .venv/bin/pytest tests/ -v
   .venv/bin/ruff check ghostwatch/ tests/
   ```

4. **Open a Pull Request** against `main`. Include:
   - A clear description of what changed and why
   - Steps to reproduce (for bug fixes)
   - Test output showing the change works

5. PRs must pass all CI checks before merging.

---

## Code Style

- **Language:** Python 3.11+, async-first.
- **Validation:** Use **Pydantic v2** for all schema and data validation.
- **Linting:** **Ruff** — run `ruff check ghostwatch/ tests/` before committing.
- **Imports:** Use `from __future__ import annotations` at the top of every module.
- **No external services:** Never add a dependency that makes a network call to a remote service during normal operation.
- **Comments:** Write comments only where logic is non-obvious.

---

## Testing Requirements

Every code change must include appropriate tests. GhostWatch uses **pytest** with **pytest-asyncio**.

Place tests in `tests/`:

```
tests/
├── test_schema.py
├── test_rules.py
├── test_redaction.py
├── test_storage.py
├── test_platform_detection.py
├── test_adapters.py          # Use mocked subprocess — never call real OS commands in tests
└── fixtures/
    └── sample_events.json
```

### Acceptance criteria

- New detection rules: include a unit test verifying the rule fires on a known input and does not fire on a clean input.
- New platform adapters: include mocked tests for the happy path, permission denied, and unavailable command cases.
- Storage changes: include tests for deduplication and ordering.
- AI client changes: include tests for unavailable server and malformed response handling.

---

## Project Structure

```
ghostwatch/
├── ghostwatch/
│   ├── ai/              # Local model client and prompt templates
│   ├── api/             # FastAPI routes
│   ├── collectors/      # psutil process snapshot collector
│   ├── core/            # Schema, rules, redaction, investigator
│   ├── platforms/       # Platform adapters (Linux/macOS) behind shared interface
│   └── storage/         # SQLite persistence
├── frontend/            # Vue 3 + Vite dashboard
├── tests/               # pytest test suite
└── docs/                # Architecture, threat model, demo guide
```

### Adding a new detection rule

1. Add a function decorated with `@rule` in `ghostwatch/core/rules.py`
2. The function must accept a `GhostEvent` and return `list[RuleFinding]`
3. Rules must be deterministic — same input always produces the same output
4. Add a unit test in `tests/test_rules.py` covering fire and no-fire cases

### Adding a new platform adapter

1. Create a class inheriting from `LogAdapter` in `ghostwatch/platforms/<platform>/`
2. Implement `async def collect(...)` returning `(list[GhostEvent], CollectorCapability)`
3. Handle missing commands, permission errors, and timeouts gracefully — never raise
4. Wire it into `ghostwatch/platforms/detect.py`
5. Add mocked tests in `tests/test_adapters.py`

---

## Non-Negotiable Constraints

| Constraint | Why |
|-----------|-----|
| **Local-only AI** | GhostWatch's privacy promise. Logs must never leave the user's machine. |
| **No cloud fallback** | If Ollama is unavailable, show events and rule findings — never silently call a remote API. |
| **AI cannot change severity** | Severity is determined by deterministic rules. AI output is explanatory only. |
| **AI cannot declare compromise** | The model must disclose uncertainty. Certainty claims are the user's to make. |
| **No command execution** | AI-generated text must never be executed as shell commands. |
| **No automatic remediation** | GhostWatch investigates — it does not terminate processes or modify system configuration. |
| **Redact before inference** | Credentials and tokens must be stripped before any event data reaches the AI. |
| **Fail safely** | Missing telemetry sources must be reported as capability status, not application errors. |

Any PR that violates these constraints will not be merged regardless of other quality.

---

## Getting Help

- Open a [GitHub Issue](https://github.com/praveen-pravi6B/ghostwatch/issues) for bugs or questions.
- Check `docs/architecture.md` for the design and data flow.
- Check `docs/threat-model.md` for trust boundaries and security assumptions.
