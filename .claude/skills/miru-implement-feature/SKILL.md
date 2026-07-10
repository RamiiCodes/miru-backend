---
name: miru-implement-feature
description: Use when implementing a new Miru backend feature using the established model/repository/schema/service/route/test pattern.
---

# Miru Backend Feature Workflow

Use this workflow for new backend features.

## Steps

1. Understand the architecture intent.
2. Check existing nearby patterns.
3. Create SQLAlchemy model if needed.
4. Register model in `app/db/models/__init__.py`.
5. Create Alembic migration if schema changes.
6. Create repository.
7. Create Pydantic schemas.
8. Create service.
9. Create FastAPI route.
10. Register route in `app/main.py`.
11. Add API integration tests.
12. Run focused tests.
13. Run `pytest -q`.

## Rules

- Do not rename existing architecture concepts.
- Do not modify unrelated systems.
- Do not weaken safety behavior.
- Do not update tests just to hide regressions.
- Prefer root-cause fixes.