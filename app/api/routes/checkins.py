from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.repositories.checkin_repository import (
    create_structured_checkin,
    get_structured_checkin_by_id,
)
from app.db.repositories.user_repository import get_user_by_id
from app.db.session import get_db
from app.schemas.checkin import StructuredCheckinCreate, StructuredCheckinRead

router = APIRouter()


@router.post("", response_model=StructuredCheckinRead, status_code=status.HTTP_201_CREATED)
def create_structured_checkin_endpoint(
    payload: StructuredCheckinCreate,
    db: Session = Depends(get_db),
):
    user = get_user_by_id(db, payload.user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )

    return create_structured_checkin(
        db=db,
        user_id=payload.user_id,
        mood_score=payload.mood_score,
        stress_score=payload.stress_score,
        energy_score=payload.energy_score,
        sleep_score=payload.sleep_score,
        social_score=payload.social_score,
    )


@router.get("/{checkin_id}", response_model=StructuredCheckinRead)
def get_structured_checkin_endpoint(
    checkin_id: UUID,
    db: Session = Depends(get_db),
):
    checkin = get_structured_checkin_by_id(db, checkin_id)

    if not checkin:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Structured check-in not found.",
        )

    return checkin