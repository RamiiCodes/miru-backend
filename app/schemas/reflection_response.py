from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ReflectionResponseRead(BaseModel):
    id: UUID
    user_id: UUID

    source_type: str
    source_id: UUID | None

    title: str
    message: str

    tone: str
    response_type: str

    suggested_action_id: UUID | None

    source_snapshot_json: dict | None

    model_version: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)