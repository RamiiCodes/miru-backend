from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class DailyReflectionRead(BaseModel):
    id: UUID
    user_id: UUID

    reflection_date: date

    title: str
    summary: str

    emotional_state_summary: str | None
    insight_summary: str | None
    pattern_summary: str | None
    action_summary: str | None

    focus_areas: list[str] | None

    source_snapshot_json: dict | None

    model_version: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)