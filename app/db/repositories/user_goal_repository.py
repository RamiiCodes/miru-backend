from uuid import UUID

from sqlalchemy.orm import Session

from app.db.models.user_goal import UserGoal


def create_user_goal(
    db: Session,
    user_id: UUID,
    source_type: str,
    source_id: UUID | None,
    category: str,
    title: str,
    description: str | None,
    priority: int,
    time_horizon: str,
    status: str,
    progress: float,
    confidence: float | None,
) -> UserGoal:
    user_goal = UserGoal(
        user_id=user_id,
        source_type=source_type,
        source_id=source_id,
        category=category,
        title=title,
        description=description,
        priority=priority,
        time_horizon=time_horizon,
        status=status,
        progress=progress,
        confidence=confidence,
    )

    db.add(user_goal)
    db.commit()
    db.refresh(user_goal)

    return user_goal


def get_user_goal_by_user_id_and_id(
    db: Session,
    user_id: UUID,
    user_goal_id: UUID,
) -> UserGoal | None:
    return (
        db.query(UserGoal)
        .filter(UserGoal.user_id == user_id)
        .filter(UserGoal.id == user_goal_id)
        .first()
    )


def list_user_goals_by_user_id(
    db: Session,
    user_id: UUID,
    include_inactive: bool = False,
) -> list[UserGoal]:
    query = db.query(UserGoal).filter(UserGoal.user_id == user_id)

    if not include_inactive:
        query = query.filter(UserGoal.status == "active")

    return (
        query.order_by(
            UserGoal.priority.desc(),
            UserGoal.created_at.desc(),
        )
        .all()
    )


def list_reasoning_user_goals_by_user_id(
    db: Session,
    user_id: UUID,
    limit: int = 10,
) -> list[UserGoal]:
    return (
        db.query(UserGoal)
        .filter(UserGoal.user_id == user_id)
        .filter(UserGoal.status == "active")
        .order_by(
            UserGoal.priority.desc(),
            UserGoal.created_at.desc(),
        )
        .limit(limit)
        .all()
    )


def update_user_goal(
    db: Session,
    user_goal: UserGoal,
    values: dict,
) -> UserGoal:
    for field_name, field_value in values.items():
        setattr(user_goal, field_name, field_value)

    db.add(user_goal)
    db.commit()
    db.refresh(user_goal)

    return user_goal