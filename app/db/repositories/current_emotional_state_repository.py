from uuid import UUID

from sqlalchemy.orm import Session

from app.db.models.current_emotional_state import CurrentEmotionalState


def create_current_emotional_state(
    db: Session,
    user_id: UUID,
    stress_level: float | None,
    energy_level: float | None,
    sleep_quality: float | None,
    social_connection: float | None,
    emotional_stability: float | None,
    motivation: float | None,
    self_esteem: float | None,
    physical_activity: float | None,
    eating_habits: float | None,
    confidence: float,
    model_version: str = "current_emotional_state_v0_1",
) -> CurrentEmotionalState:
    state = CurrentEmotionalState(
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
        model_version=model_version,
    )

    db.add(state)
    db.commit()
    db.refresh(state)

    return state


def get_latest_current_emotional_state(
    db: Session,
    user_id: UUID,
) -> CurrentEmotionalState | None:
    return (
        db.query(CurrentEmotionalState)
        .filter(CurrentEmotionalState.user_id == user_id)
        .order_by(CurrentEmotionalState.calculated_at.desc())
        .first()
    )