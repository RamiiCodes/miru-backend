from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class JournalExtractedSignalRead(BaseModel):
    id: UUID
    user_id: UUID
    journal_entry_id: UUID
    journal_analysis_id: UUID

    signal_code: str
    value: float
    confidence: float
    evidence: str | None
    reason: str | None

    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class JournalAnalysisRead(BaseModel):
    id: UUID
    user_id: UUID
    journal_entry_id: UUID

    provider: str
    model_name: str
    prompt_version: str

    status: str
    language: str | None

    summary: str | None
    emotional_tone: str | None

    safety_flags: list[str] | None
    themes: list[str] | None
    life_event_candidates_json: list[dict] | None
    raw_output_json: dict | None

    error_message: str | None
    latency_ms: int | None
    created_at: datetime

    extracted_signals: list[JournalExtractedSignalRead]

    model_config = ConfigDict(from_attributes=True)