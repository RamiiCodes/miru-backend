# Miru Project Instructions

Miru is a FastAPI backend for emotional-state tracking, reflection, and personalized guidance.

## Core principles

- Miru is not a generic chatbot.
- Miru must preserve traceability from raw input to analysis to signals to outputs.
- Safety behavior must never be weakened.
- Do not rename core architecture concepts without explicit approval.
- Do not make large architectural decisions alone.
- When unsure, ask before coding.

## Current backend architecture

Main flow:

JournalEntry
→ JournalAnalyzer
→ JournalAnalysis
→ JournalExtractedSignals
→ UserSignals
→ CurrentEmotionalState
→ Insights / Patterns / Actions / Reflections

## Backend conventions

Use the existing pattern:

1. SQLAlchemy model
2. repository
3. Pydantic schema
4. service
5. FastAPI route
6. tests
7. Alembic migration when needed

## Testing rules

- Add or update tests for every backend behavior change.
- Run focused tests first.
- Run `pytest -q` before considering work complete.
- Do not change tests only to hide a real regression.
- Prefer root-cause fixes.

## LLM policy

LLMs may extract structured data from journals.

LLMs must not freely generate final recommendations or therapy-like advice yet.

Recommendation and reflection decisions should remain controlled by backend logic until explicit approval.

## Important distinction

- UserContext = stable declared user life context.
- UserProfile = app/profile/preferences/onboarding.
- ReasoningInputAssembler = technical helper, not an architecture system.
- JournalAnalysis = stored interpretation of a JournalEntry.
- JournalExtractedSignals = extracted signals before normalization into UserSignals.