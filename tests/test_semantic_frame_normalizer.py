from app.ai.journal_analyzer import (
    AdditionalSemanticDimensionResult,
    JournalSemanticFrameResult,
    SemanticDimensionResult,
    SemanticEventCandidateResult,
)
from app.services.semantic_frame_normalizer import (
    CORE_DIMENSION_NAMES,
    normalize_semantic_frame,
)


def test_normalizer_fills_missing_core_dimensions_with_nulls():
    semantic_frame = JournalSemanticFrameResult(
        core_dimensions={
            "Valence": SemanticDimensionResult(
                value=0.9,
                confidence=0.8,
                evidence="I am happy",
                reason="Positive wording.",
            )
        },
        raw_output={
            "source": "test",
        },
    )

    normalized = normalize_semantic_frame(
        semantic_frame=semantic_frame,
    )

    assert set(normalized.core_dimensions_json.keys()) == set(CORE_DIMENSION_NAMES)

    assert normalized.core_dimensions_json["valence"] == {
        "value": 0.9,
        "confidence": 0.8,
        "evidence": "I am happy",
        "reason": "Positive wording.",
    }

    assert normalized.core_dimensions_json["arousal"] is None
    assert normalized.core_dimensions_json["threat"] is None
    assert normalized.raw_output_json == {
        "source": "test",
    }


def test_normalizer_deduplicates_and_normalizes_open_fields():
    semantic_frame = JournalSemanticFrameResult(
        emotion_labels=[
            "Happy",
            " happy ",
            "A bit overwhelmed",
        ],
        semantic_tags=[
            "Major Transition",
            "major_transition",
            "Relationship Milestone!",
            "",
        ],
        life_domains=[
            "Future Planning",
            "future_planning",
            "Relationship",
        ],
        needs=[
            " Emotional Integration ",
            "emotional_integration",
            "Connection",
        ],
        safety_flags=[
            "Severe Distress",
            "severe_distress",
        ],
    )

    normalized = normalize_semantic_frame(
        semantic_frame=semantic_frame,
    )

    assert normalized.emotion_labels_json == [
        "happy",
        "a bit overwhelmed",
    ]

    assert normalized.semantic_tags_json == [
        "major_transition",
        "relationship_milestone",
    ]

    assert normalized.life_domains_json == [
        "future_planning",
        "relationship",
    ]

    assert normalized.needs_json == [
        "emotional_integration",
        "connection",
    ]

    assert normalized.safety_flags_json == [
        "severe_distress",
    ]


def test_normalizer_normalizes_additional_dimensions():
    semantic_frame = JournalSemanticFrameResult(
        additional_dimensions=[
            AdditionalSemanticDimensionResult(
                name="Identity Transition",
                value=0.7,
                confidence=0.8,
                evidence="got engaged",
                reason="Engagement changes identity context.",
            ),
            AdditionalSemanticDimensionResult(
                name="identity_transition",
                value=0.6,
                confidence=0.7,
                evidence="duplicate",
                reason="duplicate",
            ),
        ]
    )

    normalized = normalize_semantic_frame(
        semantic_frame=semantic_frame,
    )

    assert normalized.additional_dimensions_json == [
        {
            "name": "identity_transition",
            "value": 0.7,
            "confidence": 0.8,
            "evidence": "got engaged",
            "reason": "Engagement changes identity context.",
        }
    ]


def test_normalizer_normalizes_event_candidates_without_inventing_meaning():
    semantic_frame = JournalSemanticFrameResult(
        event_candidates=[
            SemanticEventCandidateResult(
                category="Relationship",
                event_type="Got Engaged!",
                title=" Got engaged ",
                description=" The user got engaged today. ",
                significance=0.9,
                valence=0.95,
                confidence=0.95,
                evidence="I got engaged today",
                semantic_tags=[
                    "Relationship Milestone",
                    "relationship_milestone",
                ],
                life_domains=[
                    "Future Planning",
                    "relationship",
                ],
            )
        ]
    )

    normalized = normalize_semantic_frame(
        semantic_frame=semantic_frame,
    )

    assert normalized.event_candidates_json == [
        {
            "category": "relationship",
            "event_type": "got_engaged",
            "title": "Got engaged",
            "description": "The user got engaged today.",
            "significance": 0.9,
            "valence": 0.95,
            "confidence": 0.95,
            "evidence": "I got engaged today",
            "semantic_tags": [
                "relationship_milestone",
            ],
            "life_domains": [
                "future_planning",
                "relationship",
            ],
        }
    ]


def test_normalizer_preserves_raw_output():
    raw_output = {
        "source": "nvidia_direct_semantic_extraction",
        "model_name": "mistralai/mistral-medium-3.5-128b",
        "nested": {
            "value": True,
        },
    }

    semantic_frame = JournalSemanticFrameResult(
        raw_output=raw_output,
    )

    normalized = normalize_semantic_frame(
        semantic_frame=semantic_frame,
    )

    assert normalized.raw_output_json == raw_output