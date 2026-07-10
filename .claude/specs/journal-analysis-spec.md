# Journal Analysis Spec

## Status

IMPLEMENTED core architecture.

## Purpose

JournalAnalysis separates raw user writing from structured interpretation.

## Pipeline

JournalEntry
→ JournalAnalyzer
→ JournalAnalysis
→ JournalExtractedSignals
→ UserSignals

## Analyzer output

JournalAnalyzer must return:

- detected_signals
- safety_flags
- themes
- life_event_candidates
- emotional_tone
- summary
- language
- provider
- model_name
- prompt_version
- raw_output

## LLM policy

LLMs may extract structured JSON.

LLMs must not generate final advice or therapy-like reflections in this layer.