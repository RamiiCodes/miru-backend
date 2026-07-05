from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.orm import Session

from app.db.models.user_feedback import UserFeedback


def get_user_feedback_by_target(
    db: Session,
    user_id: UUID,
    target_type: str,
    target_id: UUID,
) -> UserFeedback | None:
    return (
        db.query(UserFeedback)
        .filter(
            UserFeedback.user_id == user_id,
            UserFeedback.target_type == target_type,
            UserFeedback.target_id == target_id,
        )
        .first()
    )


def upsert_user_feedback(
    db: Session,
    user_id: UUID,
    target_type: str,
    target_id: UUID,
    rating: str,
    comment: str | None,
) -> UserFeedback:
    feedback = get_user_feedback_by_target(
        db=db,
        user_id=user_id,
        target_type=target_type,
        target_id=target_id,
    )

    if feedback is None:
        feedback = UserFeedback(
            user_id=user_id,
            target_type=target_type,
            target_id=target_id,
            rating=rating,
            comment=comment,
        )
    else:
        feedback.rating = rating
        feedback.comment = comment
        feedback.updated_at = datetime.now(timezone.utc)

    db.add(feedback)
    db.commit()
    db.refresh(feedback)

    return feedback


def list_user_feedback_by_user_id(
    db: Session,
    user_id: UUID,
) -> list[UserFeedback]:
    return (
        db.query(UserFeedback)
        .filter(UserFeedback.user_id == user_id)
        .order_by(UserFeedback.created_at.desc())
        .all()
    )