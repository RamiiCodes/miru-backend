---
paths:
  - "app/ai/**/*.py"
  - "app/services/*reflection*.py"
  - "app/services/action_suggestion_service.py"
  - "app/services/journal_signal_service.py"
  - "tests/test_llm*.py"
---

# LLM Policy Rules

## Current allowed LLM role

LLMs may be used for structured extraction.

Allowed:

- detect signals
- detect themes
- detect life event candidates
- detect safety flags
- produce structured JSON following the JournalAnalyzer contract

Not allowed yet:

- freely generate final recommendations
- freely generate final therapy-like reflections
- diagnose users
- bypass backend safety rules
- bypass evidence or confidence systems

## Future direction

Later, LLMs may help phrase reflections inside backend-selected constraints.

Backend chooses strategy.
LLM writes wording.