from uuid import UUID

from sqlalchemy.orm import Session

from app.db.models.signal_catalog import SignalCatalog
from app.db.models.user_signal import UserSignal
from app.db.repositories.current_emotional_state_repository import (
    create_current_emotional_state,
)
from app.db.models.current_emotional_state import CurrentEmotionalState


SIGNAL_TO_STATE_FIELD = {
    "stress_level": "stress_level",
    "energy_level": "energy_level",
    "sleep_quality": "sleep_quality",
    "social_connection": "social_connection",
    "mood_level": "emotional_stability",
}


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


def calculate_current_emotional_state(
    db: Session,
    user_id: UUID,
) -> CurrentEmotionalState:
    latest_signals = _get_latest_signal_values_by_code(
        db=db,
        user_id=user_id,
    )

    state_values: dict[str, float | None] = {
        "stress_level": None,
        "energy_level": None,
        "sleep_quality": None,
        "social_connection": None,
        "emotional_stability": None,
        "motivation": None,
        "self_esteem": None,
        "physical_activity": None,
        "eating_habits": None,
    }

    used_confidences: list[float] = []

    for signal_code, state_field in SIGNAL_TO_STATE_FIELD.items():
        signal = latest_signals.get(signal_code)

        if signal is None:
            continue

        state_values[state_field] = signal.value
        used_confidences.append(signal.confidence)

    if used_confidences:
        confidence = round(sum(used_confidences) / len(used_confidences), 2)
    else:
        confidence = 0.0

    return create_current_emotional_state(
        db=db,
        user_id=user_id,
        stress_level=state_values["stress_level"],
        energy_level=state_values["energy_level"],
        sleep_quality=state_values["sleep_quality"],
        social_connection=state_values["social_connection"],
        emotional_stability=state_values["emotional_stability"],
        motivation=state_values["motivation"],
        self_esteem=state_values["self_esteem"],
        physical_activity=state_values["physical_activity"],
        eating_habits=state_values["eating_habits"],
        confidence=confidence,
    )