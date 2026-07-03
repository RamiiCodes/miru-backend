from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class JournalEntryCreate(BaseModel):
    user_id: UUID
    content: str = Field(min_length=1)


class JournalEntryRead(BaseModel):
    id: UUID
    user_id: UUID
    content: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)