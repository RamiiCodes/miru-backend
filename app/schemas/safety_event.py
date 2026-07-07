from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class SafetyEventRead(BaseModel):
    id: UUID
    user_id: UUID

    flag_type: str
    severity: str
    status: str

    source_type: str
    source_id: UUID

    message: str

    acknowledged_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)