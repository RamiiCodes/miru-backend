from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.db.models.safety_event import SafetyEvent
from app.db.repositories.safety_event_repository import (
    acknowledge_safety_event,
    create_safety_event,
    get_safety_event_by_id_for_user,
)


SAFETY_FLAG_SEVERITY = {
    "self_harm_risk": "high",
    "harm_to_others_risk": "high",
    "abuse_or_coercion_context": "medium",
    "severe_distress": "medium",
}


SAFETY_FLAG_MESSAGES = {
    "self_harm_risk": (
        "A possible self-harm related signal was detected from this entry."
    ),
    "harm_to_others_risk": (
        "A possible harm-to-others related signal was detected from this entry."
    ),
    "abuse_or_coercion_context": (
        "A possible abuse or coercion context was detected from this entry."
    ),
    "severe_distress": (
        "A severe distress signal was detected from this entry."
    ),
}


def create_safety_events_from_flags(
    db: Session,
    user_id: UUID,
    source_type: str,
    source_id: UUID,
    safety_flags: list[str],
) -> list[SafetyEvent]:
    created_events: list[SafetyEvent] = []

    unique_flags = sorted(set(safety_flags))

    for flag_type in unique_flags:
        if flag_type not in SAFETY_FLAG_SEVERITY:
            continue

        event = create_safety_event(
            db=db,
            user_id=user_id,
            flag_type=flag_type,
            severity=SAFETY_FLAG_SEVERITY[flag_type],
            source_type=source_type,
            source_id=source_id,
            message=SAFETY_FLAG_MESSAGES[flag_type],
        )

        created_events.append(event)

    return created_events


def acknowledge_safety_event_for_user(
    db: Session,
    user_id: UUID,
    safety_event_id: UUID,
) -> SafetyEvent:
    safety_event = get_safety_event_by_id_for_user(
        db=db,
        user_id=user_id,
        safety_event_id=safety_event_id,
    )

    if safety_event is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Safety event not found.",
        )

    return acknowledge_safety_event(
        db=db,
        safety_event=safety_event,
    )