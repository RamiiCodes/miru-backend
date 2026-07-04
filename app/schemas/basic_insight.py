from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class BasicInsightRead(BaseModel):
    id: UUID
    user_id: UUID
    state_id: UUID

    rule_code: str

    title: str
    message: str

    insight_type: str
    severity: str

    confidence: float
    model_version: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)