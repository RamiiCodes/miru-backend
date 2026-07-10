---
paths:
  - "app/services/action_suggestion_service.py"
  - "app/helpers/coping_style_action_ranker.py"
  - "app/db/models/action_suggestion.py"
  - "tests/test_action*.py"
  - "tests/test_coping_style_recommendation_flow.py"
---

# Recommendation Rules

Current code name: ActionSuggestion.

Architecture name: Recommendation System.

## Rules

- Recommendations must be grounded in state, signals, insights, patterns, context, coping style, or safety status.
- UserCopingStyle may adjust recommendation priority and confidence.
- SafetyEvents must override normal recommendation behavior.
- Do not let LLMs freely generate final recommendations yet.
- LLMs may later propose candidates, but backend must filter them.
- Do not suggest intense actions during high-severity grief or safety contexts.

## Reference

Read `.claude/specs/recommendation-system-spec.md` before non-trivial changes.