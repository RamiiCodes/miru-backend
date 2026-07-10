# LLM Analyzer Spec

## Status

DECIDED, NOT FULLY IMPLEMENTED.

## Purpose

Add future LLM provider behind the JournalAnalyzer interface.

## Allowed role

The LLM may extract structured data:

- detected signals
- themes
- life event candidates
- safety flags
- emotional tone
- short summary

## Forbidden role for now

The LLM must not freely generate:

- final recommendations
- therapy-like advice
- diagnosis
- uncontrolled reflections

## Target architecture

KeywordJournalAnalyzer
OpenAIJournalAnalyzer
ClaudeJournalAnalyzer
OllamaJournalAnalyzer

All providers must return the same JournalAnalysisResult contract.