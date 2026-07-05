from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.models.user import User
from app.db.repositories.daily_reflection_repository import (
    get_latest_daily_reflection,
    list_daily_reflections_by_user_id,
)
from app.db.session import get_db
from app.schemas.daily_reflection import DailyReflectionRead
from app.services.daily_reflection_service import generate_daily_reflection_for_user

router = APIRouter()


@router.get("", response_model=list[DailyReflectionRead])
def list_daily_reflections_endpoint(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return list_daily_reflections_by_user_id(
        db=db,
        user_id=current_user.id,
    )


@router.get("/latest", response_model=DailyReflectionRead)
def get_latest_daily_reflection_endpoint(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    reflection = get_latest_daily_reflection(
        db=db,
        user_id=current_user.id,
    )

    if reflection is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Daily reflection not found.",
        )

    return reflection


@router.post("/generate", response_model=DailyReflectionRead)
def generate_daily_reflection_endpoint(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return generate_daily_reflection_for_user(
        db=db,
        user_id=current_user.id,
    )