from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.orm import Session

from app.db.models.user_goal import UserGoal
from app.db.repositories.user_goal_repository import (
    create_user_goal,
    get_user_goal_by_user_id_and_id,
    list_user_goals_by_user_id,
    update_user_goal,
)
from app.schemas.user_goal import UserGoalCreate, UserGoalUpdate


def list_user_goals(
    db: Session,
    user_id: UUID,
    include_inactive: bool = False,
) -> list[UserGoal]:
    return list_user_goals_by_user_id(
        db=db,
        user_id=user_id,
        include_inactive=include_inactive,
    )


def create_manual_user_goal(
    db: Session,
    user_id: UUID,
    payload: UserGoalCreate,
) -> UserGoal:
    return create_user_goal(
        db=db,
        user_id=user_id,
        source_type="manual",
        source_id=None,
        category=payload.category,
        title=payload.title,
        description=payload.description,
        priority=payload.priority,
        time_horizon=payload.time_horizon,
        status="active",
        progress=0.0,
        confidence=1.0,
    )


def update_user_goal_for_user(
    db: Session,
    user_id: UUID,
    user_goal_id: UUID,
    payload: UserGoalUpdate,
) -> UserGoal | None:
    user_goal = get_user_goal_by_user_id_and_id(
        db=db,
        user_id=user_id,
        user_goal_id=user_goal_id,
    )

    if user_goal is None:
        return None

    values = payload.model_dump(exclude_unset=True)

    if "status" in values:
        values = _apply_status_side_effects(
            values=values,
            current_status=user_goal.status,
        )

    return update_user_goal(
        db=db,
        user_goal=user_goal,
        values=values,
    )


def complete_user_goal(
    db: Session,
    user_id: UUID,
    user_goal_id: UUID,
) -> UserGoal | None:
    user_goal = get_user_goal_by_user_id_and_id(
        db=db,
        user_id=user_id,
        user_goal_id=user_goal_id,
    )

    if user_goal is None:
        return None

    return update_user_goal(
        db=db,
        user_goal=user_goal,
        values={
            "status": "completed",
            "progress": 1.0,
            "completed_at": datetime.now(timezone.utc),
        },
    )


def archive_user_goal(
    db: Session,
    user_id: UUID,
    user_goal_id: UUID,
) -> UserGoal | None:
    user_goal = get_user_goal_by_user_id_and_id(
        db=db,
        user_id=user_id,
        user_goal_id=user_goal_id,
    )

    if user_goal is None:
        return None

    return update_user_goal(
        db=db,
        user_goal=user_goal,
        values={
            "status": "archived",
        },
    )


def _apply_status_side_effects(
    values: dict,
    current_status: str,
) -> dict:
    updated_values = dict(values)

    new_status = updated_values.get("status")

    if new_status == "completed":
        updated_values["progress"] = 1.0
        updated_values["completed_at"] = datetime.now(timezone.utc)

    if current_status == "completed" and new_status in ["active", "paused"]:
        updated_values["completed_at"] = None

    return updated_values