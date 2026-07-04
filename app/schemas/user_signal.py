from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class UserSignalRead(BaseModel):
    id: UUID
    user_id: UUID
    signal_id: UUID

    signal_code: str
    signal_name: str
    signal_domain: str

    value: float
    confidence: float
    source_type: str
    source_id: UUID
    recorded_at: datetime
    created_at: datetime