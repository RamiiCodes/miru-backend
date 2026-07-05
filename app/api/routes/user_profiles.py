from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.models.user import User
from app.db.repositories.user_profile_repository import (
    get_user_profile_by_user_id,
    upsert_user_profile,
)
from app.db.session import get_db
from app.schemas.user_profile import UserProfileRead, UserProfileUpdate

router = APIRouter()


@router.get("", response_model=UserProfileRead)
def get_profile_endpoint(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    profile = get_user_profile_by_user_id(
        db=db,
        user_id=current_user.id,
    )

    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User profile not found.",
        )

    return profile


@router.patch("", response_model=UserProfileRead)
def update_profile_endpoint(
    payload: UserProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    update_data = payload.model_dump(exclude_unset=True)

    return upsert_user_profile(
        db=db,
        user_id=current_user.id,
        **update_data,
    )