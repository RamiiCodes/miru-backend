# Testing Rules

## General rules

- Add tests for every new behavior.
- Run focused tests before full suite.
- Run `pytest -q` before completion.
- Do not weaken assertions unless the architecture changed.
- If tests conflict, identify the correct architecture source of truth.

## Current test database

Tests use PostgreSQL test DB:

postgresql+psycopg://miru:miru_password@localhost:5432/miru_test

## Test style

Prefer integration-style API tests using FastAPI TestClient.

Each feature should test:

- authentication required
- create/update/read flow
- user isolation
- expected side effects
- safety behavior when relevant