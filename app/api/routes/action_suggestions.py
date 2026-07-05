from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.models.user import User
from app.db.repositories.action_suggestion_repository import (
    complete_action_suggestion,
    dismiss_action_suggestion,
    get_action_suggestion_by_id,
    list_action_suggestions_by_user_id,
)
from app.db.session import get_db
from app.schemas.action_suggestion import ActionSuggestionRead
from app.services.action_suggestion_service import generate_action_suggestions_for_user

router = APIRouter()


@router.get("", response_model=list[ActionSuggestionRead])
def list_action_suggestions_endpoint(
    include_completed: bool = Query(default=False),
    include_dismissed: bool = Query(default=False),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return list_action_suggestions_by_user_id(
        db=db,
        user_id=current_user.id,
        include_completed=include_completed,
        include_dismissed=include_dismissed,
    )


@router.post("/generate", response_model=list[ActionSuggestionRead])
def generate_action_suggestions_endpoint(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return generate_action_suggestions_for_user(
        db=db,
        user_id=current_user.id,
    )


@router.patch("/{action_id}/complete", response_model=ActionSuggestionRead)
def complete_action_suggestion_endpoint(
    action_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    action = get_action_suggestion_by_id(
        db=db,
        user_id=current_user.id,
        action_id=action_id,
    )

    if action is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Action suggestion not found.",
        )

    return complete_action_suggestion(
        db=db,
        action=action,
    )


@router.patch("/{action_id}/dismiss", response_model=ActionSuggestionRead)
def dismiss_action_suggestion_endpoint(
    action_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    action = get_action_suggestion_by_id(
        db=db,
        user_id=current_user.id,
        action_id=action_id,
    )

    if action is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Action suggestion not found.",
        )

    return dismiss_action_suggestion(
        db=db,
        action=action,
    )