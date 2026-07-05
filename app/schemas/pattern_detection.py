from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class PatternDetectionRead(BaseModel):
    id: UUID
    user_id: UUID

    pattern_code: str
    title: str
    description: str

    pattern_type: str
    severity: str
    confidence: float

    evidence_json: dict | None

    window_start_date: date
    window_end_date: date
    detection_window_days: int

    model_version: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)