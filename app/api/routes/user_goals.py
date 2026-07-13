from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.models.user import User
from app.db.session import get_db
from app.schemas.user_goal import (
    UserGoalCreate,
    UserGoalRead,
    UserGoalUpdate,
)
from app.services.user_goal_service import (
    archive_user_goal,
    complete_user_goal,
    create_manual_user_goal,
    list_user_goals,
    update_user_goal_for_user,
)

router = APIRouter()


@router.get("", response_model=list[UserGoalRead])
def list_user_goals_endpoint(
    include_inactive: bool = Query(default=False),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return list_user_goals(
        db=db,
        user_id=current_user.id,
        include_inactive=include_inactive,
    )


@router.post("", response_model=UserGoalRead, status_code=201)
def create_user_goal_endpoint(
    payload: UserGoalCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return create_manual_user_goal(
        db=db,
        user_id=current_user.id,
        payload=payload,
    )


@router.patch("/{user_goal_id}", response_model=UserGoalRead)
def update_user_goal_endpoint(
    user_goal_id: UUID,
    payload: UserGoalUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    user_goal = update_user_goal_for_user(
        db=db,
        user_id=current_user.id,
        user_goal_id=user_goal_id,
        payload=payload,
    )

    if user_goal is None:
        raise HTTPException(
            status_code=404,
            detail="User goal not found.",
        )

    return user_goal


@router.patch("/{user_goal_id}/complete", response_model=UserGoalRead)
def complete_user_goal_endpoint(
    user_goal_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    user_goal = complete_user_goal(
        db=db,
        user_id=current_user.id,
        user_goal_id=user_goal_id,
    )

    if user_goal is None:
        raise HTTPException(
            status_code=404,
            detail="User goal not found.",
        )

    return user_goal


@router.patch("/{user_goal_id}/archive", response_model=UserGoalRead)
def archive_user_goal_endpoint(
    user_goal_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    user_goal = archive_user_goal(
        db=db,
        user_id=current_user.id,
        user_goal_id=user_goal_id,
    )

    if user_goal is None:
        raise HTTPException(
            status_code=404,
            detail="User goal not found.",
        )

    return user_goal