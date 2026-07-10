---
name: miru-test-fix
description: Use when fixing failing Miru tests after a backend change.
---

# Miru Test Fix Workflow

## Steps

1. Read the failing assertion.
2. Identify whether the failure is:
   - real bug
   - stale test expectation
   - architecture mismatch
   - missing fixture/seed data
3. Fix the root cause.
4. Avoid broad rewrites.
5. Run the failing test file.
6. Run related test files.
7. Run `pytest -q`.

## Rules

- Do not weaken tests without explanation.
- Do not hide regressions.
- If architecture changed, update tests to match the new source of truth.