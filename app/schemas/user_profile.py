from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


ReflectionStyle = Literal["balanced", "direct", "gentle", "detailed"]


class UserProfileUpdate(BaseModel):
    display_name: str | None = Field(default=None, max_length=150)
    birth_year: int | None = Field(default=None, ge=1900, le=2100)
    country: str | None = Field(default=None, max_length=100)
    gender: str | None = Field(default=None, max_length=100)

    living_situation: str | None = Field(default=None, max_length=150)
    relationship_status: str | None = Field(default=None, max_length=150)
    work_status: str | None = Field(default=None, max_length=150)

    main_life_context: list[str] | None = None
    interests: list[str] | None = None

    preferred_reflection_style: ReflectionStyle | None = None
    onboarding_completed: bool | None = None


class UserProfileRead(BaseModel):
    id: UUID
    user_id: UUID

    display_name: str | None
    birth_year: int | None
    country: str | None
    gender: str | None

    living_situation: str | None
    relationship_status: str | None
    work_status: str | None

    main_life_context: list[str] | None
    interests: list[str] | None

    preferred_reflection_style: str
    onboarding_completed: bool

    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)