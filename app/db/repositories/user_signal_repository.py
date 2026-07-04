from datetime import datetime
from uuid import UUID

from sqlalchemy.orm import Session

from app.db.models.user_signal import UserSignal


def get_user_signal_by_source(
    db: Session,
    source_type: str,
    source_id: UUID,
    signal_id: UUID,
) -> UserSignal | None:
    return (
        db.query(UserSignal)
        .filter(
            UserSignal.source_type == source_type,
            UserSignal.source_id == source_id,
            UserSignal.signal_id == signal_id,
        )
        .first()
    )


def create_user_signal(
    db: Session,
    user_id: UUID,
    signal_id: UUID,
    value: float,
    confidence: float,
    source_type: str,
    source_id: UUID,
    recorded_at: datetime,
) -> UserSignal:
    user_signal = UserSignal(
        user_id=user_id,
        signal_id=signal_id,
        value=value,
        confidence=confidence,
        source_type=source_type,
        source_id=source_id,
        recorded_at=recorded_at,
    )

    db.add(user_signal)
    db.commit()
    db.refresh(user_signal)

    return user_signal


def list_user_signals_by_user_id(
    db: Session,
    user_id: UUID,
) -> list[dict]:
    rows = (
        db.query(UserSignal)
        .join(UserSignal.signal)
        .filter(UserSignal.user_id == user_id)
        .order_by(UserSignal.recorded_at.desc())
        .all()
    )

    return [
        {
            "id": user_signal.id,
            "user_id": user_signal.user_id,
            "signal_id": user_signal.signal_id,
            "signal_code": user_signal.signal.code,
            "signal_name": user_signal.signal.name,
            "signal_domain": user_signal.signal.domain,
            "value": user_signal.value,
            "confidence": user_signal.confidence,
            "source_type": user_signal.source_type,
            "source_id": user_signal.source_id,
            "recorded_at": user_signal.recorded_at,
            "created_at": user_signal.created_at,
        }
        for user_signal in rows
    ]