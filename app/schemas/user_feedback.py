from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


FeedbackTargetType = Literal[
    "basic_insight",
    "action_suggestion",
    "daily_reflection",
    "pattern_detection",
]

FeedbackRating = Literal[
    "useful",
    "not_useful",
    "inaccurate",
    "too_direct",
    "too_vague",
    "not_relevant",
]


class UserFeedbackCreate(BaseModel):
    target_type: FeedbackTargetType
    target_id: UUID
    rating: FeedbackRating
    comment: str | None = Field(default=None, max_length=2000)


class UserFeedbackRead(BaseModel):
    id: UUID
    user_id: UUID

    target_type: str
    target_id: UUID

    rating: str
    comment: str | None

    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)