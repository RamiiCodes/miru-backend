from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.models.user import User
from app.db.repositories.safety_event_repository import (
    list_open_safety_events_by_user_id,
    list_safety_events_by_user_id,
)
from app.db.session import get_db
from app.schemas.safety_event import SafetyEventRead
from app.services.safety_event_service import acknowledge_safety_event_for_user

router = APIRouter()


@router.get("", response_model=list[SafetyEventRead])
def list_safety_events_endpoint(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return list_safety_events_by_user_id(
        db=db,
        user_id=current_user.id,
    )


@router.get("/open", response_model=list[SafetyEventRead])
def list_open_safety_events_endpoint(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return list_open_safety_events_by_user_id(
        db=db,
        user_id=current_user.id,
    )


@router.patch("/{safety_event_id}/acknowledge", response_model=SafetyEventRead)
def acknowledge_safety_event_endpoint(
    safety_event_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return acknowledge_safety_event_for_user(
        db=db,
        user_id=current_user.id,
        safety_event_id=safety_event_id,
    )