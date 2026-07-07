from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.orm import Session

from app.db.models.user_context import UserContext


def get_user_context_by_user_id(
    db: Session,
    user_id: UUID,
) -> UserContext | None:
    return (
        db.query(UserContext)
        .filter(UserContext.user_id == user_id)
        .first()
    )


def upsert_user_context(
    db: Session,
    user_id: UUID,
    age_range_min: int,
    age_range_max: int,
    country: str,
    work_situation: str,
    relationship_status: str,
    family_support_score: int,
    social_connection_score: int,
    work_stress_baseline: int,
) -> UserContext:
    user_context = get_user_context_by_user_id(
        db=db,
        user_id=user_id,
    )

    if user_context is None:
        user_context = UserContext(user_id=user_id)

    user_context.age_range_min = age_range_min
    user_context.age_range_max = age_range_max
    user_context.country = country
    user_context.work_situation = work_situation
    user_context.relationship_status = relationship_status
    user_context.family_support_score = family_support_score
    user_context.social_connection_score = social_connection_score
    user_context.work_stress_baseline = work_stress_baseline
    user_context.updated_at = datetime.now(timezone.utc)

    db.add(user_context)
    db.commit()
    db.refresh(user_context)

    return user_context


def patch_user_context(
    db: Session,
    user_context: UserContext,
    update_data: dict,
) -> UserContext:
    for field_name, field_value in update_data.items():
        setattr(user_context, field_name, field_value)

    user_context.updated_at = datetime.now(timezone.utc)

    db.add(user_context)
    db.commit()
    db.refresh(user_context)

    return user_context