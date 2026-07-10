# Recommendation System Spec

## Status

IMPLEMENTED as ActionSuggestion.

## Purpose

Generate practical, personalized, low-risk actions.

## Current inputs

- CurrentEmotionalState
- BasicInsights
- PatternDetections
- UserCopingStyle
- SafetyEvents

## Current behavior

UserCopingStyle can adjust:

- confidence
- priority
- ranking

## Rule

LLMs must not freely generate final recommendations yet.

Backend remains responsible for safety, filtering, and ranking.