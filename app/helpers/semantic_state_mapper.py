from dataclasses import dataclass, field
from typing import Any, Literal


TransformType = Literal["direct", "inverse"]


@dataclass(frozen=True)
class SemanticStateRule:
    semantic_signal_code: str
    state_dimension: str
    transform: TransformType
    weight: float


@dataclass(frozen=True)
class SemanticStateEstimate:
    value: float
    confidence: float
    contributing_signal_codes: list[str] = field(default_factory=list)


SEMANTIC_STATE_RULES = [
    # Generic affective tone.
    SemanticStateRule(
        semantic_signal_code="semantic_valence",
        state_dimension="emotional_stability",
        transform="direct",
        weight=1.0,
    ),
    SemanticStateRule(
        semantic_signal_code="semantic_valence",
        state_dimension="motivation",
        transform="direct",
        weight=0.35,
    ),

    # Felt threat/pressure.
    SemanticStateRule(
        semantic_signal_code="semantic_threat",
        state_dimension="stress_level",
        transform="direct",
        weight=1.0,
    ),
    SemanticStateRule(
        semantic_signal_code="semantic_threat",
        state_dimension="emotional_stability",
        transform="inverse",
        weight=0.45,
    ),

    # Sense of control/agency.
    SemanticStateRule(
        semantic_signal_code="semantic_control",
        state_dimension="stress_level",
        transform="inverse",
        weight=0.65,
    ),
    SemanticStateRule(
        semantic_signal_code="semantic_control",
        state_dimension="motivation",
        transform="direct",
        weight=0.75,
    ),

    # Social connection.
    SemanticStateRule(
        semantic_signal_code="semantic_social_connection",
        state_dimension="social_connection",
        transform="direct",
        weight=1.0,
    ),

    # Self evaluation.
    SemanticStateRule(
        semantic_signal_code="semantic_self_evaluation",
        state_dimension="self_esteem",
        transform="direct",
        weight=1.0,
    ),

    # Energy.
    SemanticStateRule(
        semantic_signal_code="semantic_energy",
        state_dimension="energy_level",
        transform="direct",
        weight=1.0,
    ),

    # Uncertainty / lack of clarity.
    SemanticStateRule(
        semantic_signal_code="semantic_uncertainty",
        state_dimension="stress_level",
        transform="direct",
        weight=0.45,
    ),
    SemanticStateRule(
        semantic_signal_code="semantic_uncertainty",
        state_dimension="emotional_stability",
        transform="inverse",
        weight=0.35,
    ),

    # Arousal is not automatically stress.
    # It can gently inform energy, but threat/control decide stress.
    SemanticStateRule(
        semantic_signal_code="semantic_arousal",
        state_dimension="energy_level",
        transform="direct",
        weight=0.25,
    ),
]


def calculate_semantic_state_estimates(
    user_signals: list[Any],
) -> dict[str, SemanticStateEstimate]:
    """
    Convert generic semantic UserSignals into state estimates.

    This function must stay generic:
    - no emotion labels
    - no life event names
    - no if grief / if joy / if engagement
    """

    latest_signals_by_code = _latest_signal_by_code(
        user_signals=user_signals,
    )

    contributions_by_dimension: dict[str, list[tuple[float, float, str]]] = {}

    for rule in SEMANTIC_STATE_RULES:
        signal = latest_signals_by_code.get(rule.semantic_signal_code)

        if signal is None:
            continue

        signal_value = _safe_score(
            _get_signal_value(signal, "value")
        )

        signal_confidence = _safe_score(
            _get_signal_value(signal, "confidence")
        )

        if signal_value is None or signal_confidence is None:
            continue

        contribution_value = _apply_transform(
            value=signal_value,
            transform=rule.transform,
        )

        contribution_weight = rule.weight * signal_confidence

        if contribution_weight <= 0:
            continue

        contributions_by_dimension.setdefault(
            rule.state_dimension,
            [],
        ).append(
            (
                contribution_value,
                contribution_weight,
                rule.semantic_signal_code,
            )
        )

    return {
        state_dimension: _combine_contributions(contributions)
        for state_dimension, contributions in contributions_by_dimension.items()
    }


def get_semantic_estimate_value(
    estimates: dict[str, SemanticStateEstimate],
    state_dimension: str,
) -> float | None:
    estimate = estimates.get(state_dimension)

    if estimate is None:
        return None

    return estimate.value


def get_semantic_estimate_confidence(
    estimates: dict[str, SemanticStateEstimate],
) -> float | None:
    if not estimates:
        return None

    confidences = [
        estimate.confidence
        for estimate in estimates.values()
    ]

    return round(
        sum(confidences) / len(confidences),
        4,
    )


def _combine_contributions(
    contributions: list[tuple[float, float, str]],
) -> SemanticStateEstimate:
    total_weight = sum(
        weight
        for _, weight, _ in contributions
    )

    if total_weight <= 0:
        return SemanticStateEstimate(
            value=0.5,
            confidence=0.0,
            contributing_signal_codes=[],
        )

    weighted_value = sum(
        value * weight
        for value, weight, _ in contributions
    ) / total_weight

    average_confidence = min(
        1.0,
        total_weight / len(contributions),
    )

    return SemanticStateEstimate(
        value=round(
            _cap_score(weighted_value),
            4,
        ),
        confidence=round(
            _cap_score(average_confidence),
            4,
        ),
        contributing_signal_codes=[
            signal_code
            for _, _, signal_code in contributions
        ],
    )


def _latest_signal_by_code(
    user_signals: list[Any],
) -> dict[str, Any]:
    latest_signals: dict[str, Any] = {}

    for signal in user_signals:
        signal_code = _get_signal_code(signal)

        if signal_code is None:
            continue

        existing_signal = latest_signals.get(signal_code)

        if existing_signal is None:
            latest_signals[signal_code] = signal
            continue

        if _signal_sort_key(signal) >= _signal_sort_key(existing_signal):
            latest_signals[signal_code] = signal

    return latest_signals


def _get_signal_code(
    signal: Any,
) -> str | None:
    if isinstance(signal, dict):
        raw_code = signal.get("signal_code") or signal.get("code")
    else:
        raw_code = (
            getattr(signal, "signal_code", None)
            or getattr(signal, "code", None)
        )

        if raw_code is None:
            signal_catalog = (
                getattr(signal, "signal_catalog", None)
                or getattr(signal, "signal", None)
            )

            if signal_catalog is not None:
                raw_code = (
                    getattr(signal_catalog, "code", None)
                    or getattr(signal_catalog, "signal_code", None)
                )

    if not isinstance(raw_code, str):
        return None

    return raw_code


def _get_signal_value(
    signal: Any,
    field_name: str,
) -> Any:
    if isinstance(signal, dict):
        return signal.get(field_name)

    return getattr(signal, field_name, None)


def _signal_sort_key(
    signal: Any,
) -> str:
    for field_name in [
        "recorded_at",
        "timestamp",
        "created_at",
    ]:
        value = _get_signal_value(signal, field_name)

        if value is not None:
            return str(value)

    return ""


def _apply_transform(
    value: float,
    transform: TransformType,
) -> float:
    if transform == "inverse":
        return 1.0 - value

    return value


def _safe_score(
    value: Any,
) -> float | None:
    if value is None:
        return None

    try:
        parsed_value = float(value)
    except (TypeError, ValueError):
        return None

    return _cap_score(parsed_value)


def _cap_score(
    value: float,
) -> float:
    return max(
        0.0,
        min(
            1.0,
            value,
        ),
    )