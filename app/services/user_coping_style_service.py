from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.db.models.user_coping_style import UserCopingStyle
from app.db.repositories.user_coping_style_repository import (
    get_user_coping_style_by_user_id,
    patch_user_coping_style,
    upsert_user_coping_style,
)
from app.schemas.user_coping_style import (
    UserCopingStyleUpdate,
    UserCopingStyleUpsert,
)


def create_or_replace_user_coping_style(
    db: Session,
    user_id: UUID,
    payload: UserCopingStyleUpsert,
) -> UserCopingStyle:
    data = payload.model_dump()

    return upsert_user_coping_style(
        db=db,
        user_id=user_id,
        **data,
    )


def update_user_coping_style_for_user(
    db: Session,
    user_id: UUID,
    payload: UserCopingStyleUpdate,
) -> UserCopingStyle:
    coping_style = get_user_coping_style_by_user_id(
        db=db,
        user_id=user_id,
    )

    if coping_style is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User coping style not found.",
        )

    update_data = payload.model_dump(exclude_unset=True)

    if not update_data:
        return coping_style

    return patch_user_coping_style(
        db=db,
        coping_style=coping_style,
        update_data=update_data,
    )