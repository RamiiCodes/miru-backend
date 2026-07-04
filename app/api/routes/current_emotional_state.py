from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.repositories.current_emotional_state_repository import (
    get_latest_current_emotional_state,
)
from app.db.repositories.user_repository import get_user_by_id
from app.db.session import get_db
from app.schemas.current_emotional_state import CurrentEmotionalStateRead
from app.services.current_emotional_state_service import (
    calculate_current_emotional_state,
)

router = APIRouter()


@router.get("/users/{user_id}", response_model=CurrentEmotionalStateRead)
def get_latest_current_emotional_state_endpoint(
    user_id: UUID,
    db: Session = Depends(get_db),
):
    user = get_user_by_id(db, user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )

    state = get_latest_current_emotional_state(db=db, user_id=user_id)

    if not state:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Current emotional state not found.",
        )

    return state


@router.post("/users/{user_id}/calculate", response_model=CurrentEmotionalStateRead)
def calculate_current_emotional_state_endpoint(
    user_id: UUID,
    db: Session = Depends(get_db),
):
    user = get_user_by_id(db, user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )

    return calculate_current_emotional_state(db=db, user_id=user_id)