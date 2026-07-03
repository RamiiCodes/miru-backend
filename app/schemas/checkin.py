from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class StructuredCheckinCreate(BaseModel):
    user_id: UUID
    mood_score: int = Field(ge=0, le=10)
    stress_score: int = Field(ge=0, le=10)
    energy_score: int = Field(ge=0, le=10)
    sleep_score: int = Field(ge=0, le=10)
    social_score: int = Field(ge=0, le=10)


class StructuredCheckinRead(BaseModel):
    id: UUID
    user_id: UUID
    mood_score: int
    stress_score: int
    energy_score: int
    sleep_score: int
    social_score: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)