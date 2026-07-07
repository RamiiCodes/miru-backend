from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.models.user import User
from app.db.repositories.user_context_repository import get_user_context_by_user_id
from app.db.session import get_db
from app.schemas.user_context import (
    UserContextRead,
    UserContextUpdate,
    UserContextUpsert,
)
from app.services.user_context_service import (
    create_or_replace_user_context,
    update_user_context_for_user,
)

router = APIRouter()


@router.get("", response_model=UserContextRead)
def get_user_context_endpoint(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    user_context = get_user_context_by_user_id(
        db=db,
        user_id=current_user.id,
    )

    if user_context is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User context not found.",
        )

    return user_context


@router.put("", response_model=UserContextRead)
def upsert_user_context_endpoint(
    payload: UserContextUpsert,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return create_or_replace_user_context(
        db=db,
        user_id=current_user.id,
        payload=payload,
    )


@router.patch("", response_model=UserContextRead)
def patch_user_context_endpoint(
    payload: UserContextUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return update_user_context_for_user(
        db=db,
        user_id=current_user.id,
        payload=payload,
    )