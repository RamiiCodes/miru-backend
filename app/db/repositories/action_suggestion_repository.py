from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.orm import Session

from app.db.models.action_suggestion import ActionSuggestion


def get_action_suggestion_by_source(
    db: Session,
    user_id: UUID,
    action_code: str,
    source_type: str,
    source_id: UUID,
) -> ActionSuggestion | None:
    return (
        db.query(ActionSuggestion)
        .filter(
            ActionSuggestion.user_id == user_id,
            ActionSuggestion.action_code == action_code,
            ActionSuggestion.source_type == source_type,
            ActionSuggestion.source_id == source_id,
        )
        .first()
    )


def get_active_action_suggestion_by_code(
    db: Session,
    user_id: UUID,
    action_code: str,
) -> ActionSuggestion | None:
    return (
        db.query(ActionSuggestion)
        .filter(ActionSuggestion.user_id == user_id)
        .filter(ActionSuggestion.action_code == action_code)
        .filter(ActionSuggestion.is_completed.is_(False))
        .filter(ActionSuggestion.is_dismissed.is_(False))
        .first()
    )


def create_action_suggestion(
    db: Session,
    user_id: UUID,
    action_code: str,
    title: str,
    description: str,
    action_type: str,
    priority: str,
    reason: str,
    source_type: str,
    source_id: UUID,
    confidence: float,
    model_version: str = "action_suggestion_v0_1",
) -> ActionSuggestion:
    existing_action = get_action_suggestion_by_source(
        db=db,
        user_id=user_id,
        action_code=action_code,
        source_type=source_type,
        source_id=source_id,
    )

    if existing_action:
        return existing_action

    action = ActionSuggestion(
        user_id=user_id,
        action_code=action_code,
        title=title,
        description=description,
        action_type=action_type,
        priority=priority,
        reason=reason,
        source_type=source_type,
        source_id=source_id,
        confidence=confidence,
        model_version=model_version,
    )

    db.add(action)
    db.commit()
    db.refresh(action)

    return action


def list_action_suggestions_by_user_id(
    db: Session,
    user_id: UUID,
    include_completed: bool = False,
    include_dismissed: bool = False,
) -> list[ActionSuggestion]:
    query = db.query(ActionSuggestion).filter(ActionSuggestion.user_id == user_id)

    if not include_completed:
        query = query.filter(ActionSuggestion.is_completed.is_(False))

    if not include_dismissed:
        query = query.filter(ActionSuggestion.is_dismissed.is_(False))

    return query.order_by(ActionSuggestion.created_at.desc()).all()


def get_action_suggestion_by_id(
    db: Session,
    user_id: UUID,
    action_id: UUID,
) -> ActionSuggestion | None:
    return (
        db.query(ActionSuggestion)
        .filter(
            ActionSuggestion.id == action_id,
            ActionSuggestion.user_id == user_id,
        )
        .first()
    )


def complete_action_suggestion(
    db: Session,
    action: ActionSuggestion,
) -> ActionSuggestion:
    action.is_completed = True
    action.completed_at = datetime.now(timezone.utc)

    db.add(action)
    db.commit()
    db.refresh(action)

    return action


def dismiss_action_suggestion(
    db: Session,
    action: ActionSuggestion,
) -> ActionSuggestion:
    action.is_dismissed = True
    action.dismissed_at = datetime.now(timezone.utc)

    db.add(action)
    db.commit()
    db.refresh(action)

    return action
