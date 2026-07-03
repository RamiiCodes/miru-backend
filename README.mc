# Miru

Miru is an AI-powered emotional state tracking and self-understanding application.

## Current Goal

Build Miru V0.1 as a backend-first MVP.

Initial vertical slice:

1. User submits a journal entry.
2. User submits a structured check-in.
3. Backend stores raw data.
4. Backend creates normalized UserSignals.
5. Backend calculates CurrentEmotionalState.
6. Backend later generates simple insights.

## Stack

- FastAPI
- PostgreSQL
- Redis
- Celery
- Qdrant later
- Python
- Docker Compose

## Important Principle

Miru does not diagnose users.

Miru stores raw user data separately from AI interpretations.