from datetime import datetime
from uuid import UUID

from sqlalchemy.orm import Session

from app.db.models.life_event import LifeEvent
from app.db.repositories.life_event_repository import (
    confirm_life_event,
    create_life_event,
    dismiss_life_event,
    get_life_event_by_source_and_event_type,
    get_life_event_by_user_id_and_id,
    list_life_events_by_user_id,
)
from app.schemas.life_event import LifeEventConfirmRequest, LifeEventCreate


EVENT_TYPE_TO_CATEGORY = {
    "bereavement": "family",
    "death_of_loved_one": "family",
    "divorce": "family",
    "birth_of_child": "family",
    "marriage": "relationship",
    "engagement": "relationship",
    "breakup": "relationship",
    "job_loss": "career",
    "career_promotion": "career",
    "graduation": "education",
    "serious_illness": "health",
    "surgery": "health",
    "financial_hardship": "financial",
    "relocation": "relocation",
    "immigration": "relocation",
    "legal_issue": "legal",
    "major_accident": "trauma",
    "assault": "trauma",
    "natural_disaster": "trauma",
    "achievement": "achievement",
    "personal_growth": "personal_growth",
}


EVENT_TYPE_TO_TITLE = {
    "bereavement": "Death of someone close",
    "death_of_loved_one": "Death of someone close",
    "divorce": "Divorce",
    "birth_of_child": "Birth of a child",
    "marriage": "Marriage",
    "engagement": "Got engaged",
    "breakup": "Breakup",
    "job_loss": "Job loss",
    "career_promotion": "Career promotion",
    "graduation": "Graduation",
    "serious_illness": "Serious illness",
    "surgery": "Surgery",
    "financial_hardship": "Financial hardship",
    "relocation": "Relocation",
    "immigration": "Relocation to a new country",
    "legal_issue": "Legal event",
    "major_accident": "Major accident",
    "assault": "Traumatic event",
    "natural_disaster": "Natural disaster",
    "achievement": "Major achievement",
    "personal_growth": "Personal milestone",
}


def list_user_life_events(
    db: Session,
    user_id: UUID,
    include_dismissed: bool = False,
) -> list[LifeEvent]:
    return list_life_events_by_user_id(
        db=db,
        user_id=user_id,
        include_dismissed=include_dismissed,
    )


def create_manual_life_event(
    db: Session,
    user_id: UUID,
    payload: LifeEventCreate,
) -> LifeEvent:
    return create_life_event(
        db=db,
        user_id=user_id,
        source_type="manual",
        source_id=None,
        category=payload.category,
        event_type=_normalize_event_type(payload.event_type),
        title=payload.title,
        description=payload.description,
        emotional_impact=payload.emotional_impact,
        event_date=payload.event_date,
        event_date_precision=payload.event_date_precision,
        confirmation_status="confirmed",
        confidence=1.0,
        evidence=None,
    )


def confirm_user_life_event(
    db: Session,
    user_id: UUID,
    life_event_id: UUID,
    payload: LifeEventConfirmRequest,
) -> LifeEvent | None:
    life_event = get_life_event_by_user_id_and_id(
        db=db,
        user_id=user_id,
        life_event_id=life_event_id,
    )

    if life_event is None:
        return None

    return confirm_life_event(
        db=db,
        life_event=life_event,
        confirmation_status=payload.confirmation_status,
        title=payload.title,
        description=payload.description,
        category=payload.category,
        event_date=payload.event_date,
        event_date_precision=payload.event_date_precision,
        emotional_impact=payload.emotional_impact,
    )


def dismiss_user_life_event(
    db: Session,
    user_id: UUID,
    life_event_id: UUID,
) -> LifeEvent | None:
    life_event = get_life_event_by_user_id_and_id(
        db=db,
        user_id=user_id,
        life_event_id=life_event_id,
    )

    if life_event is None:
        return None

    return dismiss_life_event(
        db=db,
        life_event=life_event,
    )


def create_life_events_from_journal_analysis(
    db: Session,
    user_id: UUID,
    journal_analysis_id: UUID,
    life_event_candidates: list[dict],
    minimum_confidence: float = 0.6,
) -> list[LifeEvent]:
    created_events: list[LifeEvent] = []

    for candidate in life_event_candidates:
        event_type = _normalize_event_type(
            str(candidate.get("event_type") or "unknown_life_event")
        )

        confidence = _safe_float(candidate.get("confidence"))

        if confidence is not None and confidence < minimum_confidence:
            continue

        existing_event = get_life_event_by_source_and_event_type(
            db=db,
            user_id=user_id,
            source_type="journal_analysis",
            source_id=journal_analysis_id,
            event_type=event_type,
        )

        if existing_event is not None:
            continue

        category = _category_for_event_type(event_type)
        title = _title_for_candidate(event_type=event_type, candidate=candidate)

        created_event = create_life_event(
            db=db,
            user_id=user_id,
            source_type="journal_analysis",
            source_id=journal_analysis_id,
            category=category,
            event_type=event_type,
            title=title,
            description=candidate.get("description"),
            emotional_impact=None,
            event_date=None,
            event_date_precision="unknown",
            confirmation_status="candidate",
            confidence=confidence,
            evidence=candidate.get("evidence"),
        )

        created_events.append(created_event)

    return created_events


def _normalize_event_type(event_type: str) -> str:
    return (
        event_type.strip()
        .lower()
        .replace(" ", "_")
        .replace("-", "_")
    )


def _category_for_event_type(event_type: str) -> str:
    return EVENT_TYPE_TO_CATEGORY.get(event_type, "other")


def _title_for_candidate(
    event_type: str,
    candidate: dict,
) -> str:
    known_title = EVENT_TYPE_TO_TITLE.get(event_type)

    if known_title is not None:
        return known_title

    description = candidate.get("description")

    if description:
        return str(description)[:255]

    return event_type.replace("_", " ").title()


def _safe_float(value) -> float | None:
    if value is None:
        return None

    try:
        parsed_value = float(value)
    except (TypeError, ValueError):
        return None

    return max(0.0, min(1.0, parsed_value))
