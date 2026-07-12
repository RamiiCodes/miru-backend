from datetime import datetime
from uuid import UUID

from sqlalchemy.orm import Session

from app.db.models.life_event import LifeEvent


def create_life_event(
    db: Session,
    user_id: UUID,
    source_type: str,
    source_id: UUID | None,
    category: str,
    event_type: str,
    title: str,
    description: str | None,
    emotional_impact: int | None,
    event_date: datetime | None,
    event_date_precision: str,
    confirmation_status: str,
    confidence: float | None,
    evidence: str | None,
) -> LifeEvent:
    life_event = LifeEvent(
        user_id=user_id,
        source_type=source_type,
        source_id=source_id,
        category=category,
        event_type=event_type,
        title=title,
        description=description,
        emotional_impact=emotional_impact,
        event_date=event_date,
        event_date_precision=event_date_precision,
        confirmation_status=confirmation_status,
        confidence=confidence,
        evidence=evidence,
    )

    db.add(life_event)
    db.commit()
    db.refresh(life_event)

    return life_event


def get_life_event_by_user_id_and_id(
    db: Session,
    user_id: UUID,
    life_event_id: UUID,
) -> LifeEvent | None:
    return (
        db.query(LifeEvent)
        .filter(LifeEvent.user_id == user_id)
        .filter(LifeEvent.id == life_event_id)
        .first()
    )


def get_life_event_by_source_and_event_type(
    db: Session,
    user_id: UUID,
    source_type: str,
    source_id: UUID,
    event_type: str,
) -> LifeEvent | None:
    return (
        db.query(LifeEvent)
        .filter(LifeEvent.user_id == user_id)
        .filter(LifeEvent.source_type == source_type)
        .filter(LifeEvent.source_id == source_id)
        .filter(LifeEvent.event_type == event_type)
        .first()
    )


def list_life_events_by_user_id(
    db: Session,
    user_id: UUID,
    include_dismissed: bool = False,
) -> list[LifeEvent]:
    query = db.query(LifeEvent).filter(LifeEvent.user_id == user_id)

    if not include_dismissed:
        query = query.filter(LifeEvent.confirmation_status != "dismissed")

    return (
        query.order_by(
            LifeEvent.event_date.desc().nullslast(),
            LifeEvent.created_at.desc(),
        )
        .all()
    )


def confirm_life_event(
    db: Session,
    life_event: LifeEvent,
    confirmation_status: str,
    title: str | None = None,
    description: str | None = None,
    category: str | None = None,
    event_date: datetime | None = None,
    event_date_precision: str | None = None,
    emotional_impact: int | None = None,
) -> LifeEvent:
    life_event.confirmation_status = confirmation_status

    if title is not None:
        life_event.title = title

    if description is not None:
        life_event.description = description

    if category is not None:
        life_event.category = category

    if event_date is not None:
        life_event.event_date = event_date

    if event_date_precision is not None:
        life_event.event_date_precision = event_date_precision

    if emotional_impact is not None:
        life_event.emotional_impact = emotional_impact

    db.add(life_event)
    db.commit()
    db.refresh(life_event)

    return life_event


def dismiss_life_event(
    db: Session,
    life_event: LifeEvent,
) -> LifeEvent:
    life_event.confirmation_status = "dismissed"
    life_event.is_active = False

    db.add(life_event)
    db.commit()
    db.refresh(life_event)

    return life_event