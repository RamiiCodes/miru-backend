from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ActionSuggestionRead(BaseModel):
    id: UUID
    user_id: UUID

    action_code: str
    title: str
    description: str

    action_type: str
    priority: str
    reason: str

    source_type: str
    source_id: UUID

    confidence: float

    is_completed: bool
    is_dismissed: bool

    completed_at: datetime | None
    dismissed_at: datetime | None

    model_version: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)