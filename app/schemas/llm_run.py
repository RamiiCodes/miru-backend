from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class LLMRunRead(BaseModel):
    id: UUID
    user_id: UUID

    source_type: str
    source_id: UUID

    provider: str
    model_name: str
    prompt_version: str

    input_text: str
    output_json: dict | None

    status: str
    error_message: str | None
    latency_ms: int | None

    created_at: datetime

    model_config = ConfigDict(from_attributes=True)