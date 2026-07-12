from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.models.user import User
from app.db.session import get_db
from app.schemas.life_event import (
    LifeEventConfirmRequest,
    LifeEventCreate,
    LifeEventRead,
)
from app.services.life_event_service import (
    confirm_user_life_event,
    create_manual_life_event,
    dismiss_user_life_event,
    list_user_life_events,
)

router = APIRouter()


@router.get("", response_model=list[LifeEventRead])
def list_life_events_endpoint(
    include_dismissed: bool = Query(default=False),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return list_user_life_events(
        db=db,
        user_id=current_user.id,
        include_dismissed=include_dismissed,
    )


@router.post("", response_model=LifeEventRead, status_code=201)
def create_life_event_endpoint(
    payload: LifeEventCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return create_manual_life_event(
        db=db,
        user_id=current_user.id,
        payload=payload,
    )


@router.patch("/{life_event_id}/confirm", response_model=LifeEventRead)
def confirm_life_event_endpoint(
    life_event_id: UUID,
    payload: LifeEventConfirmRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    life_event = confirm_user_life_event(
        db=db,
        user_id=current_user.id,
        life_event_id=life_event_id,
        payload=payload,
    )

    if life_event is None:
        raise HTTPException(
            status_code=404,
            detail="Life event not found.",
        )

    return life_event


@router.patch("/{life_event_id}/dismiss", response_model=LifeEventRead)
def dismiss_life_event_endpoint(
    life_event_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    life_event = dismiss_user_life_event(
        db=db,
        user_id=current_user.id,
        life_event_id=life_event_id,
    )

    if life_event is None:
        raise HTTPException(
            status_code=404,
            detail="Life event not found.",
        )

    return life_event