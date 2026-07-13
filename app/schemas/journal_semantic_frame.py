from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class JournalSemanticFrameRead(BaseModel):
    id: UUID
    user_id: UUID
    journal_entry_id: UUID
    journal_analysis_id: UUID

    provider: str
    model_name: str | None
    prompt_version: str | None

    core_dimensions_json: dict[str, Any]
    emotion_labels_json: list[Any]
    semantic_tags_json: list[Any]
    life_domains_json: list[Any]
    needs_json: list[Any]
    additional_dimensions_json: list[Any]
    event_candidates_json: list[Any]
    safety_flags_json: list[Any]

    overall_confidence: float | None = Field(default=None, ge=0, le=1)
    raw_output_json: dict[str, Any]

    created_at: datetime

    model_config = ConfigDict(from_attributes=True)