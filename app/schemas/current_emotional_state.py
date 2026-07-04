from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class CurrentEmotionalStateRead(BaseModel):
    id: UUID
    user_id: UUID

    stress_level: float | None
    energy_level: float | None
    sleep_quality: float | None
    social_connection: float | None
    emotional_stability: float | None

    motivation: float | None
    self_esteem: float | None
    physical_activity: float | None
    eating_habits: float | None

    confidence: float
    model_version: str
    calculated_at: datetime

    model_config = ConfigDict(from_attributes=True)