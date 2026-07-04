from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.models.user import User
from app.db.repositories.current_emotional_state_repository import (
    get_latest_current_emotional_state,
)
from app.db.session import get_db
from app.schemas.current_emotional_state import CurrentEmotionalStateRead
from app.services.current_emotional_state_service import (
    calculate_current_emotional_state,
)

router = APIRouter()


@router.get("", response_model=CurrentEmotionalStateRead)
def get_latest_current_emotional_state_endpoint(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    state = get_latest_current_emotional_state(
        db=db,
        user_id=current_user.id,
    )

    if not state:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Current emotional state not found.",
        )

    return state


@router.post("/calculate", response_model=CurrentEmotionalStateRead)
def calculate_current_emotional_state_endpoint(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return calculate_current_emotional_state(
        db=db,
        user_id=current_user.id,
    )