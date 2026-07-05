from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.db.models.action_suggestion import ActionSuggestion
from app.db.models.basic_insight import BasicInsight
from app.db.models.daily_reflection import DailyReflection
from app.db.models.pattern_detection import PatternDetection
from app.db.models.user_feedback import UserFeedback
from app.db.repositories.user_feedback_repository import upsert_user_feedback


def _target_exists_for_user(
    db: Session,
    user_id: UUID,
    target_type: str,
    target_id: UUID,
) -> bool:
    if target_type == "basic_insight":
        return (
            db.query(BasicInsight)
            .filter(
                BasicInsight.id == target_id,
                BasicInsight.user_id == user_id,
            )
            .first()
            is not None
        )

    if target_type == "action_suggestion":
        return (
            db.query(ActionSuggestion)
            .filter(
                ActionSuggestion.id == target_id,
                ActionSuggestion.user_id == user_id,
            )
            .first()
            is not None
        )

    if target_type == "daily_reflection":
        return (
            db.query(DailyReflection)
            .filter(
                DailyReflection.id == target_id,
                DailyReflection.user_id == user_id,
            )
            .first()
            is not None
        )

    if target_type == "pattern_detection":
        return (
            db.query(PatternDetection)
            .filter(
                PatternDetection.id == target_id,
                PatternDetection.user_id == user_id,
            )
            .first()
            is not None
        )

    return False


def create_or_update_user_feedback(
    db: Session,
    user_id: UUID,
    target_type: str,
    target_id: UUID,
    rating: str,
    comment: str | None,
) -> UserFeedback:
    if not _target_exists_for_user(
        db=db,
        user_id=user_id,
        target_type=target_type,
        target_id=target_id,
    ):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Feedback target not found.",
        )

    return upsert_user_feedback(
        db=db,
        user_id=user_id,
        target_type=target_type,
        target_id=target_id,
        rating=rating,
        comment=comment,
    )