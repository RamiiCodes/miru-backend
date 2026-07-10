---
name: miru-llm-analyzer
description: Use when adding or modifying an LLM-based JournalAnalyzer provider for Miru.
---

# Miru LLM Analyzer Workflow

## Purpose

Add an LLM provider behind the existing JournalAnalyzer contract.

## Rules

- LLM must return structured JSON only.
- LLM must not generate final recommendations.
- LLM must not generate therapy-like reflections.
- LLM must not diagnose the user.
- LLM output must be validated with Pydantic.
- Invalid LLM output must fail safely.
- Store result in JournalAnalysis.
- Store extracted signals in JournalExtractedSignals.
- UserSignals must come from JournalExtractedSignals.

## Required tests

- valid structured extraction
- malformed JSON handling
- safety flag preservation
- user isolation
- fallback behavior if provider fails