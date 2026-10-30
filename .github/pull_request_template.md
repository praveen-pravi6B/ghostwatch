## Summary

<!-- What does this PR do? 1-3 bullet points -->

-
-

## Type of change

- [ ] Bug fix
- [ ] New detection rule
- [ ] New platform adapter
- [ ] New feature
- [ ] Security fix
- [ ] Refactor / cleanup
- [ ] Documentation
- [ ] Dependency update

## Related issue

Closes #<!-- issue number -->

## How to test

```bash

```

## Checklist

- [ ] `.venv/bin/pytest tests/ -v` passes
- [ ] `.venv/bin/ruff check ghostwatch/ tests/` passes
- [ ] No secrets or credentials in code or commits
- [ ] Local-first — no remote data transmission added
- [ ] AI remains advisory — does not change severity or execute commands
- [ ] Graceful degradation — missing sources reported as capability status, not errors
- [ ] Documentation updated if behaviour changed
