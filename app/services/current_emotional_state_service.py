from uuid import UUID

from sqlalchemy.orm import Session

from app.db.models.current_emotional_state import CurrentEmotionalState
from app.db.models.signal_catalog import SignalCatalog
from app.db.models.user_signal import UserSignal
from app.db.repositories.current_emotional_state_repository import (
    create_current_emotional_state,
)


SIGNAL_TO_STATE_FIELD = {
    "stress_level": "stress_level",
    "energy_level": "energy_level",
    "sleep_quality": "sleep_quality",
    "social_connection": "social_connection",
    "mood_level": "emotional_stability",
}


def _clamp(value: float) -> float:
    return round(max(0.0, min(1.0, value)), 2)


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


def _get_signal_value(
    latest_signals: dict[str, UserSignal],
    signal_code: str,
) -> float | None:
    signal = latest_signals.get(signal_code)

    if signal is None:
        return None

    return signal.value


def _collect_confidences(
    latest_signals: dict[str, UserSignal],
    signal_codes: list[str],
) -> list[float]:
    confidences: list[float] = []

    for signal_code in signal_codes:
        signal = latest_signals.get(signal_code)

        if signal is not None:
            confidences.append(signal.confidence)

    return confidences


def calculate_current_emotional_state(
    db: Session,
    user_id: UUID,
) -> CurrentEmotionalState:
    latest_signals = _get_latest_signal_values_by_code(
        db=db,
        user_id=user_id,
    )

    mood_level = _get_signal_value(latest_signals, "mood_level")
    stress_signal = _get_signal_value(latest_signals, "stress_level")
    energy_level = _get_signal_value(latest_signals, "energy_level")
    sleep_quality = _get_signal_value(latest_signals, "sleep_quality")
    social_connection = _get_signal_value(latest_signals, "social_connection")

    rumination = _get_signal_value(latest_signals, "rumination_tendency")
    self_criticism = _get_signal_value(latest_signals, "self_criticism")
    fear_of_failure = _get_signal_value(latest_signals, "fear_of_failure")
    work_sensitivity = _get_signal_value(latest_signals, "work_sensitivity")

    # Base structured values
    stress_level = stress_signal
    emotional_stability = mood_level

    # Journal-derived cognitive influence
    if stress_level is not None:
        if rumination is not None:
            stress_level += rumination * 0.15

        if work_sensitivity is not None:
            stress_level += work_sensitivity * 0.10

        stress_level = _clamp(stress_level)

    if emotional_stability is not None:
        if rumination is not None:
            emotional_stability -= rumination * 0.15

        if fear_of_failure is not None:
            emotional_stability -= fear_of_failure * 0.10

        emotional_stability = _clamp(emotional_stability)

    # Derived cognitive state fields
    motivation = None
    if fear_of_failure is not None:
        motivation = _clamp(1.0 - fear_of_failure)

    self_esteem = None
    if self_criticism is not None:
        self_esteem = _clamp(1.0 - self_criticism)

    physical_activity = None
    eating_habits = None

    used_confidences = _collect_confidences(
        latest_signals=latest_signals,
        signal_codes=[
            "mood_level",
            "stress_level",
            "energy_level",
            "sleep_quality",
            "social_connection",
            "rumination_tendency",
            "self_criticism",
            "fear_of_failure",
            "work_sensitivity",
        ],
    )

    if used_confidences:
        confidence = round(sum(used_confidences) / len(used_confidences), 2)
    else:
        confidence = 0.0

    return create_current_emotional_state(
        db=db,
        user_id=user_id,
        stress_level=stress_level,
        energy_level=energy_level,
        sleep_quality=sleep_quality,
        social_connection=social_connection,
        emotional_stability=emotional_stability,
        motivation=motivation,
        self_esteem=self_esteem,
        physical_activity=physical_activity,
        eating_habits=eating_habits,
        confidence=confidence,
        model_version="current_emotional_state_v0_2",
    )