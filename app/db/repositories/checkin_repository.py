from uuid import UUID

from sqlalchemy.orm import Session

from app.db.models.structured_checkin import StructuredCheckin


def create_structured_checkin(
    db: Session,
    user_id: UUID,
    mood_score: int,
    stress_score: int,
    energy_score: int,
    sleep_score: int,
    social_score: int,
) -> StructuredCheckin:
    checkin = StructuredCheckin(
        user_id=user_id,
        mood_score=mood_score,
        stress_score=stress_score,
        energy_score=energy_score,
        sleep_score=sleep_score,
        social_score=social_score,
    )

    db.add(checkin)
    db.commit()
    db.refresh(checkin)

    return checkin


def get_structured_checkin_by_id(
    db: Session,
    checkin_id: UUID,
) -> StructuredCheckin | None:
    return (
        db.query(StructuredCheckin)
        .filter(StructuredCheckin.id == checkin_id)
        .first()
    )