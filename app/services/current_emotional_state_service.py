from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.orm import Session

from app.db.models.current_emotional_state import CurrentEmotionalState
from app.db.models.signal_catalog import SignalCatalog
from app.db.models.user_signal import UserSignal


MODEL_VERSION = "current_emotional_state_v0_3"


def _clamp(value: float | None) -> float | None:
    if value is None:
        return None

    return max(0.0, min(1.0, round(value, 2)))


def _get_user_signal_catalog_fk_column():
    if hasattr(UserSignal, "signal_catalog_id"):
        return UserSignal.signal_catalog_id

    if hasattr(UserSignal, "signal_id"):
        return UserSignal.signal_id

    raise AttributeError(
        "UserSignal must expose either 'signal_catalog_id' or 'signal_id'."
    )


def _load_latest_signal_values(
    db: Session,
    user_id: UUID,
) -> dict[str, dict[str, float]]:
    signal_catalog_fk_column = _get_user_signal_catalog_fk_column()

    rows = (
        db.query(
            SignalCatalog.code,
            UserSignal.value,
            UserSignal.confidence,
            UserSignal.recorded_at,
        )
        .join(
            SignalCatalog,
            signal_catalog_fk_column == SignalCatalog.id,
        )
        .filter(UserSignal.user_id == user_id)
        .order_by(UserSignal.recorded_at.desc())
        .all()
    )

    latest_signals: dict[str, dict[str, float]] = {}

    for code, value, confidence, _recorded_at in rows:
        if code in latest_signals:
            continue

        latest_signals[code] = {
            "value": value,
            "confidence": confidence,
        }

    return latest_signals


def _signal_value(
    latest_signals: dict[str, dict[str, float]],
    signal_code: str,
) -> float | None:
    signal = latest_signals.get(signal_code)

    if signal is None:
        return None

    return signal["value"]


def _signal_confidence(
    latest_signals: dict[str, dict[str, float]],
    signal_code: str,
) -> float | None:
    signal = latest_signals.get(signal_code)

    if signal is None:
        return None

    return signal["confidence"]


def _has_meaningful_signal(value: float | None, threshold: float = 0.5) -> bool:
    return value is not None and value >= threshold


def _calculate_confidence(
    latest_signals: dict[str, dict[str, float]],
    used_signal_codes: list[str],
) -> float:
    confidences = [
        _signal_confidence(latest_signals, signal_code)
        for signal_code in used_signal_codes
    ]

    valid_confidences = [
        confidence
        for confidence in confidences
        if confidence is not None
    ]

    if not valid_confidences:
        return 0.3

    return _clamp(sum(valid_confidences) / len(valid_confidences)) or 0.3


def _get_or_create_current_state(
    db: Session,
    user_id: UUID,
) -> CurrentEmotionalState:
    current_state = (
        db.query(CurrentEmotionalState)
        .filter(CurrentEmotionalState.user_id == user_id)
        .first()
    )

    if current_state is not None:
        return current_state

    current_state = CurrentEmotionalState(user_id=user_id)

    db.add(current_state)
    db.flush()

    return current_state


def calculate_current_emotional_state(
    db: Session,
    user_id: UUID,
) -> CurrentEmotionalState:
    latest_signals = _load_latest_signal_values(
        db=db,
        user_id=user_id,
    )

    mood_level = _signal_value(latest_signals, "mood_level")
    stress_level = _signal_value(latest_signals, "stress_level")
    energy_level = _signal_value(latest_signals, "energy_level")
    sleep_quality = _signal_value(latest_signals, "sleep_quality")
    social_connection = _signal_value(latest_signals, "social_connection")

    rumination_tendency = _signal_value(latest_signals, "rumination_tendency")
    self_criticism = _signal_value(latest_signals, "self_criticism")
    fear_of_failure = _signal_value(latest_signals, "fear_of_failure")
    work_sensitivity = _signal_value(latest_signals, "work_sensitivity")

    grief_loss = _signal_value(latest_signals, "grief_loss")
    emotional_numbness = _signal_value(latest_signals, "emotional_numbness")
    disorientation = _signal_value(latest_signals, "disorientation")
    loneliness = _signal_value(latest_signals, "loneliness")
    overwhelm = _signal_value(latest_signals, "overwhelm")

    used_signal_codes = list(latest_signals.keys())

    emotional_stability = mood_level
    motivation = None
    self_esteem = None

    stress_related_signals_present = any(
        [
            _has_meaningful_signal(rumination_tendency),
            _has_meaningful_signal(work_sensitivity),
            _has_meaningful_signal(overwhelm),
            _has_meaningful_signal(grief_loss),
            _has_meaningful_signal(disorientation),
        ]
    )

    if stress_level is None and stress_related_signals_present:
        stress_level = 0.5

    emotional_stability_related_signals_present = any(
        [
            _has_meaningful_signal(rumination_tendency),
            _has_meaningful_signal(fear_of_failure),
            _has_meaningful_signal(self_criticism),
            _has_meaningful_signal(grief_loss),
            _has_meaningful_signal(emotional_numbness),
            _has_meaningful_signal(overwhelm),
            _has_meaningful_signal(disorientation),
        ]
    )

    if emotional_stability is None and emotional_stability_related_signals_present:
        emotional_stability = 0.5

    if _has_meaningful_signal(rumination_tendency):
        if stress_level is not None:
            stress_level += 0.15

        if emotional_stability is not None:
            emotional_stability -= 0.15

    if _has_meaningful_signal(work_sensitivity):
        if stress_level is not None:
            stress_level += 0.10

    if _has_meaningful_signal(overwhelm):
        if stress_level is None:
            stress_level = 0.5

        stress_level += 0.20

        if emotional_stability is not None:
            emotional_stability -= 0.15

    if _has_meaningful_signal(grief_loss):
        if stress_level is None:
            stress_level = 0.5

        stress_level += 0.15

        if emotional_stability is not None:
            emotional_stability -= 0.20

    if _has_meaningful_signal(emotional_numbness):
        if emotional_stability is not None:
            emotional_stability -= 0.15

    if _has_meaningful_signal(disorientation):
        if stress_level is None:
            stress_level = 0.5

        stress_level += 0.10

        if emotional_stability is not None:
            emotional_stability -= 0.10

    if _has_meaningful_signal(loneliness):
        if social_connection is None:
            social_connection = 1 - loneliness
        else:
            social_connection -= 0.10

    if fear_of_failure is not None:
        motivation = 1 - fear_of_failure

        if _has_meaningful_signal(fear_of_failure):
            if emotional_stability is not None:
                emotional_stability -= 0.10

    if self_criticism is not None:
        self_esteem = 1 - self_criticism

    current_state = _get_or_create_current_state(
        db=db,
        user_id=user_id,
    )

    current_state.stress_level = _clamp(stress_level)
    current_state.energy_level = _clamp(energy_level)
    current_state.sleep_quality = _clamp(sleep_quality)
    current_state.social_connection = _clamp(social_connection)
    current_state.emotional_stability = _clamp(emotional_stability)
    current_state.motivation = _clamp(motivation)
    current_state.self_esteem = _clamp(self_esteem)

    current_state.physical_activity = None
    current_state.eating_habits = None

    current_state.confidence = _calculate_confidence(
        latest_signals=latest_signals,
        used_signal_codes=used_signal_codes,
    )
    current_state.model_version = MODEL_VERSION
    current_state.calculated_at = datetime.now(timezone.utc)

    db.add(current_state)
    db.commit()
    db.refresh(current_state)

    return current_state