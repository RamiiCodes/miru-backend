from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


UserGoalCategory = Literal[
    "stress_management",
    "sleep",
    "emotional_awareness",
    "self_esteem",
    "social_connection",
    "work_life_balance",
    "grief_processing",
    "habit_building",
    "personal_growth",
    "mental_clarity",
    "other",
]

UserGoalTimeHorizon = Literal[
    "short_term",
    "medium_term",
    "long_term",
    "ongoing",
]

UserGoalStatus = Literal[
    "active",
    "paused",
    "completed",
    "archived",
]


class UserGoalCreate(BaseModel):
    category: UserGoalCategory
    title: str = Field(min_length=1, max_length=255)
    description: str | None = None
    priority: int = Field(default=5, ge=1, le=10)
    time_horizon: UserGoalTimeHorizon = "ongoing"


class UserGoalUpdate(BaseModel):
    category: UserGoalCategory | None = None
    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    priority: int | None = Field(default=None, ge=1, le=10)
    time_horizon: UserGoalTimeHorizon | None = None
    status: UserGoalStatus | None = None
    progress: float | None = Field(default=None, ge=0, le=1)


class UserGoalRead(BaseModel):
    id: UUID
    user_id: UUID

    source_type: str
    source_id: UUID | None

    category: str
    title: str
    description: str | None

    priority: int
    time_horizon: str
    status: str
    progress: float
    confidence: float | None

    completed_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)