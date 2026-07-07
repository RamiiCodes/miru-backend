from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.orm import Session

from app.db.models.user_coping_style import UserCopingStyle


def get_user_coping_style_by_user_id(
    db: Session,
    user_id: UUID,
) -> UserCopingStyle | None:
    return (
        db.query(UserCopingStyle)
        .filter(UserCopingStyle.user_id == user_id)
        .first()
    )


def upsert_user_coping_style(
    db: Session,
    user_id: UUID,
    preferred_coping_styles: list[str] | None,
    disliked_coping_styles: list[str] | None,
    writing_preference_score: int,
    movement_preference_score: int,
    breathing_preference_score: int,
    social_support_preference_score: int,
    reflection_preference_score: int,
    structure_preference_score: int,
) -> UserCopingStyle:
    coping_style = get_user_coping_style_by_user_id(
        db=db,
        user_id=user_id,
    )

    if coping_style is None:
        coping_style = UserCopingStyle(user_id=user_id)

    coping_style.preferred_coping_styles = preferred_coping_styles
    coping_style.disliked_coping_styles = disliked_coping_styles
    coping_style.writing_preference_score = writing_preference_score
    coping_style.movement_preference_score = movement_preference_score
    coping_style.breathing_preference_score = breathing_preference_score
    coping_style.social_support_preference_score = social_support_preference_score
    coping_style.reflection_preference_score = reflection_preference_score
    coping_style.structure_preference_score = structure_preference_score
    coping_style.updated_at = datetime.now(timezone.utc)

    db.add(coping_style)
    db.commit()
    db.refresh(coping_style)

    return coping_style


def patch_user_coping_style(
    db: Session,
    coping_style: UserCopingStyle,
    update_data: dict,
) -> UserCopingStyle:
    for field_name, field_value in update_data.items():
        setattr(coping_style, field_name, field_value)

    coping_style.updated_at = datetime.now(timezone.utc)

    db.add(coping_style)
    db.commit()
    db.refresh(coping_style)

    return coping_style