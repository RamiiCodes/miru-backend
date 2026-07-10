# UserContext Spec

## Status

IMPLEMENTED.

## Purpose

UserContext stores stable user-declared life context.

## Current fields

- age_range_min
- age_range_max
- country
- work_situation
- relationship_status
- family_support_score
- social_connection_score
- work_stress_baseline

## Distinctions

UserContext is not UserProfile.

UserContext is not ReasoningInputAssembler.

UserContext may influence reasoning but must not be treated as diagnosis.