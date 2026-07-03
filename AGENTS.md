# Miru — Codex Project Instructions

## Project Identity

Miru is an AI-powered emotional state tracking and self-understanding application.

Miru is not a diagnosis tool, not a therapy replacement, and not a medical product.

The goal is to help users:
- track emotional states,
- write journals,
- detect recurring patterns,
- reflect on experiences,
- receive evidence-informed recommendations,
- understand themselves over time.

## Core Architecture

The core Miru cognitive flow is:

Inputs
→ UserSignals
→ CurrentEmotionalState
→ EmotionalStateHistory
→ PatternDetections
→ InfluenceGraph
→ PsychologicalProfile
→ Insights / Reflections / Recommendations
→ UserFeedback / RecommendationHistory / UserTrust
→ Learning loop

## MVP V0.1 Scope

Implement only the smallest vertical slice first:

- FastAPI backend
- PostgreSQL database
- journal entry submission
- structured check-in submission
- UserSignals creation
- basic CurrentEmotionalState calculation
- LLMRun tracking
- simple journal analysis worker
- basic insight generation

Do not implement the full architecture at once.

## Backend Stack

Use:

- Python
- FastAPI
- PostgreSQL
- SQLAlchemy or SQLModel
- Alembic
- Redis
- Celery
- Qdrant later
- Docker Compose
- pytest

Start as a modular monolith. Do not create microservices yet.

## AI Rules

LLMs may help extract, summarize, or phrase outputs.

LLMs must not:
- diagnose the user,
- invent unsupported recommendations,
- create arbitrary signal names,
- bypass EvidenceInterventions,
- overwrite raw user data,
- make clinical claims,
- produce final outputs without validation.

All AI interpretations must be:
- traceable,
- versioned,
- confidence-scored,
- linked to source data.

## Data Rules

Raw user data is immutable.

Examples:
- JournalEntries are raw memory.
- StructuredCheckins are raw self-report.
- ReflectionResponses are raw user correction/clarification.

AI-generated interpretations must be stored separately.

Do not overwrite raw user content with AI summaries.

## Recommendation Rules

Recommendations must eventually be grounded in EvidenceInterventions.

For MVP, recommendations can be skipped or mocked if the evidence layer is not ready.

Do not let the LLM freely invent advice.

## Safety Rules

Never implement diagnosis logic.

Avoid names like:
- disorder_detector
- diagnosis_engine
- clinical_labeler

Prefer names like:
- signal_processor
- insight_generator
- reflection_service
- recommendation_service
- safety_filter

Use cautious wording:
- “may”
- “seems”
- “possible pattern”
- “worth exploring”

Avoid absolute wording:
- “this proves”
- “you are”
- “you have”

## Coding Style

Use clean, simple Python.

Prefer:
- small services,
- repository layer,
- typed schemas,
- explicit models,
- tests for core logic,
- clear error handling.

Avoid:
- over-engineering,
- premature microservices,
- hidden magic,
- giant files,
- business logic inside route handlers.

## Project Structure Target

Use this general structure:

app/
  api/
    routes/
  core/
  db/
    models/
    repositories/
  schemas/
  services/
  ai/
    llm/
    prompts/
    embeddings/
    retrieval/
    safety/
  workers/
  tests/

## Development Rule

Before generating large code changes:
1. explain the planned files,
2. keep changes small,
3. preserve the MVP scope,
4. do not add unrelated architecture,
5. do not implement future systems unless requested.

## Testing Rule

When adding a feature, add or suggest tests.

Use pytest.

Important test areas:
- API health endpoint
- journal creation
- check-in creation
- UserSignals creation
- CurrentEmotionalState calculation
- LLM output validation
- no unsupported signal names
- no diagnosis wording

## Current Priority

The next implementation priority is:

1. create FastAPI skeleton,
2. add health endpoint,
3. add PostgreSQL connection,
4. add first models,
5. add journal API,
6. add check-in API,
7. add UserSignals,
8. add basic state calculation.