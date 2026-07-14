from types import SimpleNamespace

from app.helpers.semantic_state_mapper import (
    calculate_semantic_state_estimates,
    get_semantic_estimate_confidence,
    get_semantic_estimate_value,
)


def _signal(
    signal_code: str,
    value: float,
    confidence: float = 1.0,
    created_at: str = "2026-07-14T10:00:00Z",
):
    return SimpleNamespace(
        signal_code=signal_code,
        value=value,
        confidence=confidence,
        created_at=created_at,
    )


def test_semantic_threat_increases_stress_without_emotion_label_rules():
    estimates = calculate_semantic_state_estimates(
        [
            _signal("semantic_threat", 0.85, 0.9),
        ]
    )

    assert get_semantic_estimate_value(
        estimates,
        "stress_level",
    ) == 0.85

    assert estimates["stress_level"].contributing_signal_codes == [
        "semantic_threat",
    ]


def test_low_control_increases_stress_generically():
    estimates = calculate_semantic_state_estimates(
        [
            _signal("semantic_control", 0.2, 0.9),
        ]
    )

    assert get_semantic_estimate_value(
        estimates,
        "stress_level",
    ) == 0.8


def test_valence_updates_emotional_stability_generically():
    estimates = calculate_semantic_state_estimates(
        [
            _signal("semantic_valence", 0.9, 0.9),
        ]
    )

    assert get_semantic_estimate_value(
        estimates,
        "emotional_stability",
    ) == 0.9


def test_social_connection_updates_social_connection_generically():
    estimates = calculate_semantic_state_estimates(
        [
            _signal("semantic_social_connection", 0.95, 0.9),
        ]
    )

    assert get_semantic_estimate_value(
        estimates,
        "social_connection",
    ) == 0.95


def test_energy_signal_updates_energy_generically():
    estimates = calculate_semantic_state_estimates(
        [
            _signal("semantic_energy", 0.8, 0.9),
        ]
    )

    assert get_semantic_estimate_value(
        estimates,
        "energy_level",
    ) == 0.8


def test_multiple_semantic_dimensions_are_weighted_together():
    estimates = calculate_semantic_state_estimates(
        [
            _signal("semantic_threat", 0.8, 1.0),
            _signal("semantic_control", 0.2, 1.0),
            _signal("semantic_uncertainty", 0.6, 1.0),
        ]
    )

    stress_level = get_semantic_estimate_value(
        estimates,
        "stress_level",
    )

    assert stress_level is not None
    assert 0.7 <= stress_level <= 0.8


def test_latest_signal_wins_per_semantic_code():
    estimates = calculate_semantic_state_estimates(
        [
            _signal(
                "semantic_valence",
                0.2,
                0.9,
                created_at="2026-07-14T10:00:00Z",
            ),
            _signal(
                "semantic_valence",
                0.9,
                0.9,
                created_at="2026-07-14T11:00:00Z",
            ),
        ]
    )

    assert get_semantic_estimate_value(
        estimates,
        "emotional_stability",
    ) == 0.9


def test_semantic_confidence_is_available():
    estimates = calculate_semantic_state_estimates(
        [
            _signal("semantic_valence", 0.9, 0.8),
            _signal("semantic_social_connection", 0.9, 0.6),
        ]
    )

    confidence = get_semantic_estimate_confidence(
        estimates,
    )

    assert confidence is not None
    assert 0.0 <= confidence <= 1.0