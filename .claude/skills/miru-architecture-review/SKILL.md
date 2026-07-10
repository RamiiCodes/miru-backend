---
name: miru-architecture-review
description: Use when reviewing whether a code change respects Miru architecture.
---

# Miru Architecture Review Workflow

Review the change against Miru architecture.

## Check

- Does the change preserve traceability?
- Does it respect JournalEntry → JournalAnalysis → JournalExtractedSignals → UserSignals?
- Does it preserve safety behavior?
- Does it confuse UserContext, UserProfile, or ReasoningInputAssembler?
- Does it introduce uncontrolled LLM behavior?
- Does it bypass services or repositories?
- Does it break user isolation?
- Does it add tests for new behavior?

## Output format

Return:

1. Architecture status: PASS / RISK / FAIL
2. Main risks
3. Files needing review
4. Suggested fixes