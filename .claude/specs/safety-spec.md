# Safety Spec

## Status

IMPLEMENTED early version.

## Purpose

SafetyEvents track risk signals detected from user input.

## Current safety flags

- self_harm_risk
- harm_to_others_risk
- abuse_or_coercion_context
- severe_distress

## Rules

- SafetyEvents must override normal reflection and recommendation behavior.
- SafetyEvents must be visible through API.
- SafetyEvents can be acknowledged.
- Safety behavior must not be weakened during refactors.