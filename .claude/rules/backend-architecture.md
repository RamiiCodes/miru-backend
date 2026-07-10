# Backend Architecture Rules

Applies to all backend work.

## Rules

- Follow the existing model/repository/schema/service/route/test pattern.
- Do not put business logic directly in routes.
- Do not bypass services for cognitive behavior.
- Do not rename architecture concepts without explicit approval.
- Keep helpers clearly separated from cognitive systems.
- Prefer small focused changes over broad rewrites.
- Preserve user isolation in every query.

## Current major systems

- Auth
- UserProfile
- UserContext
- UserCopingStyle
- JournalAnalysis
- UserSignals
- CurrentEmotionalState
- Insights
- PatternDetections
- ActionSuggestions
- DailyReflections
- ReflectionResponses
- SafetyEvents
- LLMRuns