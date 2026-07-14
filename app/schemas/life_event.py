from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


LifeEventCategory = Literal[
    "family",
    "relationship",
    "career",
    "education",
    "health",
    "financial",
    "relocation",
    "legal",
    "trauma",
    "achievement",
    "personal_growth",
    "other",
]

LifeEventDatePrecision = Literal[
    "unknown",
    "year",
    "month",
    "day",
    "exact",
]

LifeEventConfirmationStatus = Literal[
    "candidate",
    "confirmed",
    "partially_confirmed",
    "dismissed",
]


class LifeEventCreate(BaseModel):
    category: LifeEventCategory
    event_type: str = Field(min_length=1, max_length=100)
    title: str = Field(min_length=1, max_length=255)
    description: str | None = None
    emotional_impact: int | None = Field(default=None, ge=1, le=10)
    event_date: datetime | None = None
    event_date_precision: LifeEventDatePrecision = "unknown"


class LifeEventConfirmRequest(BaseModel):
    confirmation_status: Literal["confirmed", "partially_confirmed"] = "confirmed"

    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    category: LifeEventCategory | None = None

    emotional_impact: int | None = Field(default=None, ge=1, le=10)

    event_date: datetime | None = None
    event_date_precision: LifeEventDatePrecision | None = None


class LifeEventRead(BaseModel):
    id: UUID
    user_id: UUID

    source_type: str
    source_id: UUID | None

    source_semantic_frame_id: UUID | None

    significance: float | None
    valence: float | None
    semantic_tags_json: list
    life_domains_json: list

    category: str
    event_type: str
    title: str
    description: str | None

    emotional_impact: int | None
    event_date: datetime | None
    event_date_precision: str

    confirmation_status: str
    confidence: float | None
    significance: float | None
    valence: float | None
    semantic_tags_json: list
    life_domains_json: list
    evidence: str | None

    is_active: bool
    version: int
    supersedes_event_id: UUID | None

    detected_at: datetime
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)