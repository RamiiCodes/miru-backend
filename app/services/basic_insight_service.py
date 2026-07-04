from uuid import UUID

from sqlalchemy.orm import Session

from app.db.models.basic_insight import BasicInsight
from app.db.models.signal_catalog import SignalCatalog
from app.db.models.user_signal import UserSignal
from app.db.repositories.basic_insight_repository import create_basic_insight
from app.db.repositories.current_emotional_state_repository import (
    get_latest_current_emotional_state,
)


def _get_latest_signal_values_by_code(
    db: Session,
    user_id: UUID,
) -> dict[str, UserSignal]:
    rows = (
        db.query(UserSignal, SignalCatalog.code)
        .join(SignalCatalog, UserSignal.signal_id == SignalCatalog.id)
        .filter(UserSignal.user_id == user_id)
        .order_by(UserSignal.recorded_at.desc())
        .all()
    )

    latest_by_code: dict[str, UserSignal] = {}

    for user_signal, signal_code in rows:
        if signal_code not in latest_by_code:
            latest_by_code[signal_code] = user_signal

    return latest_by_code


def _signal_value(
    latest_signals: dict[str, UserSignal],
    signal_code: str,
) -> float | None:
    signal = latest_signals.get(signal_code)

    if signal is None:
        return None

    return signal.value


def generate_basic_insights(
    db: Session,
    user_id: UUID,
) -> list[BasicInsight]:
    state = get_latest_current_emotional_state(
        db=db,
        user_id=user_id,
    )

    if state is None:
        return []

    latest_signals = _get_latest_signal_values_by_code(
        db=db,
        user_id=user_id,
    )

    rumination = _signal_value(latest_signals, "rumination_tendency")
    self_criticism = _signal_value(latest_signals, "self_criticism")
    fear_of_failure = _signal_value(latest_signals, "fear_of_failure")
    work_sensitivity = _signal_value(latest_signals, "work_sensitivity")

    insights_to_create: list[dict] = []

    if (
        state.stress_level is not None
        and state.stress_level >= 0.75
        and rumination is not None
        and rumination >= 0.5
    ):
        insights_to_create.append(
            {
                "rule_code": "stress_rumination_connection",
                "title": "Stress may be linked to repetitive thinking",
                "message": (
                    "Your recent signals suggest that repetitive thinking may be "
                    "contributing to your current stress level."
                ),
                "insight_type": "cognitive_pattern",
                "severity": "high" if state.stress_level >= 0.85 else "medium",
                "confidence": 0.68,
            }
        )

    if (
        state.self_esteem is not None
        and state.self_esteem <= 0.5
        and self_criticism is not None
        and self_criticism >= 0.5
    ):
        insights_to_create.append(
            {
                "rule_code": "self_criticism_self_esteem_connection",
                "title": "Self-critical thoughts may be affecting self-esteem",
                "message": (
                    "Your journal signals suggest self-critical language. This may be "
                    "connected to your current self-esteem score."
                ),
                "insight_type": "self_perception",
                "severity": "medium",
                "confidence": 0.65,
            }
        )

    if (
        state.motivation is not None
        and state.motivation <= 0.5
        and fear_of_failure is not None
        and fear_of_failure >= 0.5
    ):
        insights_to_create.append(
            {
                "rule_code": "fear_failure_motivation_connection",
                "title": "Fear of failure may be reducing motivation",
                "message": (
                    "Your signals suggest that fear of failure may be one factor "
                    "lowering your current motivation."
                ),
                "insight_type": "motivation_pattern",
                "severity": "medium",
                "confidence": 0.64,
            }
        )

    if (
        state.stress_level is not None
        and state.stress_level >= 0.7
        and work_sensitivity is not None
        and work_sensitivity >= 0.4
    ):
        insights_to_create.append(
            {
                "rule_code": "work_context_stress_connection",
                "title": "Work context may be influencing stress",
                "message": (
                    "Your recent entries contain work-related signals, and your stress "
                    "level is currently elevated. Work context may be an active influence."
                ),
                "insight_type": "contextual_pattern",
                "severity": "medium",
                "confidence": 0.62,
            }
        )

    if (
        state.sleep_quality is not None
        and state.sleep_quality <= 0.45
        and state.stress_level is not None
        and state.stress_level >= 0.7
    ):
        insights_to_create.append(
            {
                "rule_code": "low_sleep_high_stress_connection",
                "title": "Low sleep quality may be linked with higher stress",
                "message": (
                    "Your current state shows lower sleep quality alongside elevated "
                    "stress. This combination may be worth tracking over time."
                ),
                "insight_type": "physiological_pattern",
                "severity": "medium",
                "confidence": 0.6,
            }
        )

    if (
        state.stress_level is not None
        and state.stress_level <= 0.4
        and state.emotional_stability is not None
        and state.emotional_stability >= 0.6
    ):
        insights_to_create.append(
            {
                "rule_code": "stable_low_stress_state",
                "title": "Your current state appears relatively stable",
                "message": (
                    "Your latest signals show lower stress and stronger emotional "
                    "stability compared with high-alert patterns."
                ),
                "insight_type": "positive_state",
                "severity": "low",
                "confidence": 0.66,
            }
        )

    created_insights: list[BasicInsight] = []

    for insight_data in insights_to_create:
        created_insight = create_basic_insight(
            db=db,
            user_id=user_id,
            state_id=state.id,
            rule_code=insight_data["rule_code"],
            title=insight_data["title"],
            message=insight_data["message"],
            insight_type=insight_data["insight_type"],
            severity=insight_data["severity"],
            confidence=insight_data["confidence"],
        )

        created_insights.append(created_insight)

    return created_insights