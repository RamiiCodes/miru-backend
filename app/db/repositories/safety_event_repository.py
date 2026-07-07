from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.orm import Session

from app.db.models.safety_event import SafetyEvent


def get_safety_event_by_source_flag(
    db: Session,
    user_id: UUID,
    source_type: str,
    source_id: UUID,
    flag_type: str,
) -> SafetyEvent | None:
    return (
        db.query(SafetyEvent)
        .filter(
            SafetyEvent.user_id == user_id,
            SafetyEvent.source_type == source_type,
            SafetyEvent.source_id == source_id,
            SafetyEvent.flag_type == flag_type,
        )
        .first()
    )


def create_safety_event(
    db: Session,
    user_id: UUID,
    flag_type: str,
    severity: str,
    source_type: str,
    source_id: UUID,
    message: str,
) -> SafetyEvent:
    existing_event = get_safety_event_by_source_flag(
        db=db,
        user_id=user_id,
        source_type=source_type,
        source_id=source_id,
        flag_type=flag_type,
    )

    if existing_event is not None:
        return existing_event

    event = SafetyEvent(
        user_id=user_id,
        flag_type=flag_type,
        severity=severity,
        source_type=source_type,
        source_id=source_id,
        message=message,
    )

    db.add(event)
    db.commit()
    db.refresh(event)

    return event


def list_safety_events_by_user_id(
    db: Session,
    user_id: UUID,
) -> list[SafetyEvent]:
    return (
        db.query(SafetyEvent)
        .filter(SafetyEvent.user_id == user_id)
        .order_by(SafetyEvent.created_at.desc())
        .all()
    )


def list_open_safety_events_by_user_id(
    db: Session,
    user_id: UUID,
) -> list[SafetyEvent]:
    return (
        db.query(SafetyEvent)
        .filter(
            SafetyEvent.user_id == user_id,
            SafetyEvent.status == "open",
        )
        .order_by(SafetyEvent.created_at.desc())
        .all()
    )


def get_safety_event_by_id_for_user(
    db: Session,
    user_id: UUID,
    safety_event_id: UUID,
) -> SafetyEvent | None:
    return (
        db.query(SafetyEvent)
        .filter(
            SafetyEvent.id == safety_event_id,
            SafetyEvent.user_id == user_id,
        )
        .first()
    )


def acknowledge_safety_event(
    db: Session,
    safety_event: SafetyEvent,
) -> SafetyEvent:
    safety_event.status = "acknowledged"
    safety_event.acknowledged_at = datetime.now(timezone.utc)
    safety_event.updated_at = datetime.now(timezone.utc)

    db.add(safety_event)
    db.commit()
    db.refresh(safety_event)

    return safety_event