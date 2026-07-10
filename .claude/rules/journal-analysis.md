---
paths:
  - "app/ai/**/*.py"
  - "app/services/journal_signal_service.py"
  - "app/db/models/journal*.py"
  - "app/db/repositories/journal_analysis_repository.py"
  - "app/schemas/journal_analysis.py"
  - "app/api/routes/journal_analyses.py"
  - "tests/test_journal*.py"
---

# Journal Analysis Rules

Correct architecture:

JournalEntry
→ JournalAnalyzer
→ JournalAnalysis
→ JournalExtractedSignals
→ UserSignals

## Rules

- Do not create UserSignals directly from JournalEntry.
- UserSignals created from journals must use `source_type = "journal_extracted_signal"`.
- JournalAnalyzer providers must return structured extraction.
- JournalAnalyzer providers must not generate final advice, recommendations, or therapy-like reflections.
- Safety flags from JournalAnalysis must still create SafetyEvents.
- Keep KeywordJournalAnalyzer as fallback unless explicitly asked to remove it.
- Do not collapse JournalAnalysis and JournalExtractedSignals into UserSignals.

## Reference

Read `.claude/specs/journal-analysis-spec.md` before non-trivial changes.