---
paths:
  - "app/services/safety_event_service.py"
  - "app/db/models/safety_event.py"
  - "app/api/routes/safety_events.py"
  - "app/services/reflection_response_service.py"
  - "app/services/action_suggestion_service.py"
  - "app/ai/**/*.py"
  - "tests/test_safety*.py"
---

# Safety Rules

## Rules

- Safety behavior must never be weakened.
- SafetyEvents must override normal reflection/recommendation behavior.
- Do not generate intense recommendations when open SafetyEvents exist.
- Journal safety flags must create SafetyEvents.
- Do not let LLMs bypass safety checks.
- Do not remove safety tests.
- Avoid diagnosis or clinical certainty.

## Safety flags

Current safety flags include:

- self_harm_risk
- harm_to_others_risk
- abuse_or_coercion_context
- severe_distress

## Reference

Read `.claude/specs/safety-spec.md` before non-trivial changes.