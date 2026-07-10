---
paths:
  - "app/db/models/user_context.py"
  - "app/db/repositories/user_context_repository.py"
  - "app/schemas/user_context.py"
  - "app/services/user_context_service.py"
  - "app/api/routes/user_context.py"
  - "app/helpers/reasoning_input_assembler.py"
  - "tests/test_user_context*.py"
---

# UserContext Rules

UserContext is Miru architecture A.3 stable declared context.

## Rules

- UserContext is not UserProfile.
- UserContext is not ReasoningInputAssembler.
- UserContext stores stable user-declared life context.
- Do not merge UserContext into UserProfile.
- Do not use UserContext as a temporary DTO.
- UserContext may influence reflections, recommendations, and state interpretation.
- UserContext must not be treated as diagnosis.

## Reference

Read `.claude/specs/user-context-spec.md` before non-trivial changes.