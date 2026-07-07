from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.db.models.user_context import UserContext
from app.db.repositories.user_context_repository import (
    get_user_context_by_user_id,
    patch_user_context,
    upsert_user_context,
)
from app.schemas.user_context import UserContextUpdate, UserContextUpsert


def create_or_replace_user_context(
    db: Session,
    user_id: UUID,
    payload: UserContextUpsert,
) -> UserContext:
    data = payload.model_dump()

    return upsert_user_context(
        db=db,
        user_id=user_id,
        **data,
    )


def update_user_context_for_user(
    db: Session,
    user_id: UUID,
    payload: UserContextUpdate,
) -> UserContext:
    user_context = get_user_context_by_user_id(
        db=db,
        user_id=user_id,
    )

    if user_context is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User context not found.",
        )

    update_data = payload.model_dump(exclude_unset=True)

    if not update_data:
        return user_context

    age_range_min = update_data.get(
        "age_range_min",
        user_context.age_range_min,
    )
    age_range_max = update_data.get(
        "age_range_max",
        user_context.age_range_max,
    )

    if age_range_min > age_range_max:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="age_range_min must be lower than or equal to age_range_max.",
        )

    return patch_user_context(
        db=db,
        user_context=user_context,
        update_data=update_data,
    )