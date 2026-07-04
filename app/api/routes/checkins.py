from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.services.checkin_signal_service import create_user_signals_from_checkin

from app.services.current_emotional_state_service import calculate_current_emotional_state

from app.db.repositories.checkin_repository import (
    create_structured_checkin,
    get_structured_checkin_by_id,
)

from app.db.session import get_db
from app.schemas.checkin import StructuredCheckinCreate, StructuredCheckinRead

from app.api.deps import get_current_user
from app.db.models.user import User

router = APIRouter()


@router.post("", response_model=StructuredCheckinRead, status_code=status.HTTP_201_CREATED)
def create_structured_checkin_endpoint(
    payload: StructuredCheckinCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    checkin = create_structured_checkin(
        db=db,
        user_id=current_user.id,
        mood_score=payload.mood_score,
        stress_score=payload.stress_score,
        energy_score=payload.energy_score,
        sleep_score=payload.sleep_score,
        social_score=payload.social_score,
    )

    create_user_signals_from_checkin(db=db, checkin=checkin)

    calculate_current_emotional_state(db=db, user_id=current_user.id)

    return checkin

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