# GhostWatch — Threat Model

GhostWatch is a local investigation tool, not a security product. This document describes what it protects against, what it does not, and where the trust boundaries are.

## What GhostWatch protects

| Concern | How addressed |
|---------|--------------|
| Sensitive logs sent to cloud AI | Ollama client validates localhost-only URL; no remote fallback |
| Credentials in log content sent to AI | Redaction layer strips tokens, passwords, and API keys before inference |
| API accessible from other machines | FastAPI bound to `127.0.0.1` only; CORS restricted to localhost origins |
| AI-generated commands executed | No command execution anywhere in the codebase |
| Automatic process termination | Not implemented; by design |
| Log content treated as instructions | Prompt clearly separates system instructions from user-supplied data |

## What GhostWatch does NOT protect against

- **A compromised local machine.** If the OS is already compromised, local tools cannot be trusted.
- **Guaranteed malware detection.** GhostWatch applies heuristics. A sophisticated attacker can evade them.
- **Processes that start and exit between snapshots.** psutil polling misses short-lived processes.
- **Encrypted or obfuscated process names.** Rules operate on observable fields only.
- **Kernel-level activity.** No eBPF, no kernel module, no syscall tracing.

## Trust boundaries

```
TRUSTED                          UNTRUSTED
───────────────────────────────────────────────────────
GhostWatch Python code           Log content from OS
Pydantic schema validation       Process command lines
Deterministic rules              AI model output
Redaction layer
Ollama model weights (local)
SQLite database (local file)
```

## AI trust

The local model is treated as an untrusted assistant:

- It receives only redacted, schema-validated event data.
- Its output is validated against a strict Pydantic schema before use.
- It cannot declare the system "compromised" — the prompt explicitly prohibits this.
- Its output is displayed separately from deterministic rule findings.
- It has no ability to execute code, modify files, or make network requests.

## Data retention

- Events are stored in a local SQLite file (`ghostwatch.db`).
- The `DELETE /api/events` endpoint clears all stored events.
- No data is written outside the working directory.
- No logs are sent anywhere.
