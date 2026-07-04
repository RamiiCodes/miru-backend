from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class UserSignalRead(BaseModel):
    id: UUID
    user_id: UUID
    signal_id: UUID
    value: float
    confidence: float
    source_type: str
    source_id: UUID
    recorded_at: datetime
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)