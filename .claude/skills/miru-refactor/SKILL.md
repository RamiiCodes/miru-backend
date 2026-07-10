---
name: miru-refactor
description: Use when refactoring existing Miru backend code while preserving behavior and tests.
---

# Miru Refactor Workflow

## Steps

1. Identify current behavior.
2. Identify target architecture.
3. List files that should change.
4. Avoid unrelated edits.
5. Preserve public API unless explicitly asked.
6. Preserve user isolation.
7. Preserve safety behavior.
8. Update tests only when architecture source of truth changed.
9. Run focused tests.
10. Run `pytest -q`.

## Rules

- Do not refactor across too many systems at once.
- Do not rename concepts without approval.
- If tests conflict, explain the architecture source of truth.