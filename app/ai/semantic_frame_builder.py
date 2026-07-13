from app.ai.journal_analyzer import (
    DetectedJournalSignal,
    JournalSemanticFrameResult,
    LifeEventCandidate,
    SemanticEventCandidateResult,
)


SEVERITY_TO_SIGNIFICANCE = {
    "low": 0.3,
    "medium": 0.6,
    "high": 0.9,
}


def build_semantic_frame_from_legacy_analysis(
    detected_signals: list[DetectedJournalSignal],
    safety_flags: list[str],
    themes: list[str],
    life_event_candidates: list[LifeEventCandidate],
    emotional_tone: str | None,
    provider: str,
    model_name: str,
    prompt_version: str,
) -> JournalSemanticFrameResult:
    """
    Compatibility bridge for Phase 1.

    This does not try to be the final semantic intelligence layer.
    It preserves existing analyzer meaning inside the new generic semantic frame shape.
    Phase 2 will update the LLM prompt to produce this frame directly.
    """

    emotion_labels = _emotion_labels_from_emotional_tone(emotional_tone)

    event_candidates = [
        SemanticEventCandidateResult(
            category=None,
            event_type=candidate.event_type,
            title=None,
            description=candidate.description,
            significance=SEVERITY_TO_SIGNIFICANCE.get(candidate.severity),
            valence=None,
            confidence=candidate.confidence,
            evidence=candidate.evidence,
            semantic_tags=[],
            life_domains=[],
        )
        for candidate in life_event_candidates
    ]

    signal_confidences = [
        signal.confidence
        for signal in detected_signals
    ]

    event_confidences = [
        candidate.confidence
        for candidate in life_event_candidates
    ]

    all_confidences = signal_confidences + event_confidences

    overall_confidence = (
        sum(all_confidences) / len(all_confidences)
        if all_confidences
        else None
    )

    return JournalSemanticFrameResult(
        core_dimensions={},
        emotion_labels=emotion_labels,
        semantic_tags=_dedupe_strings(themes),
        life_domains=[],
        needs=[],
        additional_dimensions=[],
        event_candidates=event_candidates,
        safety_flags=_dedupe_strings(safety_flags),
        overall_confidence=overall_confidence,
        raw_output={
            "source": "legacy_analyzer_compatibility_bridge",
            "provider": provider,
            "model_name": model_name,
            "prompt_version": prompt_version,
            "detected_signal_codes": [
                signal.signal_code
                for signal in detected_signals
            ],
        },
    )


def _emotion_labels_from_emotional_tone(
    emotional_tone: str | None,
) -> list[str]:
    if emotional_tone is None:
        return []

    return _dedupe_strings(
        [
            part.strip()
            for part in emotional_tone.split(",")
            if part.strip()
        ]
    )


def _dedupe_strings(values: list[str]) -> list[str]:
    seen_values: set[str] = set()
    deduped_values: list[str] = []

    for value in values:
        normalized_value = value.strip()

        if not normalized_value:
            continue

        if normalized_value in seen_values:
            continue

        seen_values.add(normalized_value)
        deduped_values.append(normalized_value)

    return deduped_values