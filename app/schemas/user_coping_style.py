from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


ALLOWED_COPING_STYLES = {
    "writing",
    "movement",
    "breathing",
    "social_support",
    "reflection",
    "structure",
    "distraction",
    "rest",
}


def _validate_coping_styles(values: list[str] | None) -> list[str] | None:
    if values is None:
        return None

    unique_values = list(dict.fromkeys(values))

    invalid_values = [
        value
        for value in unique_values
        if value not in ALLOWED_COPING_STYLES
    ]

    if invalid_values:
        raise ValueError(
            f"Unsupported coping style(s): {', '.join(invalid_values)}."
        )

    return unique_values


class UserCopingStyleUpsert(BaseModel):
    preferred_coping_styles: list[str] | None = None
    disliked_coping_styles: list[str] | None = None

    writing_preference_score: int = Field(ge=0, le=10)
    movement_preference_score: int = Field(ge=0, le=10)
    breathing_preference_score: int = Field(ge=0, le=10)
    social_support_preference_score: int = Field(ge=0, le=10)
    reflection_preference_score: int = Field(ge=0, le=10)
    structure_preference_score: int = Field(ge=0, le=10)

    @field_validator("preferred_coping_styles", "disliked_coping_styles")
    @classmethod
    def validate_coping_styles(cls, values: list[str] | None) -> list[str] | None:
        return _validate_coping_styles(values)


class UserCopingStyleUpdate(BaseModel):
    preferred_coping_styles: list[str] | None = None
    disliked_coping_styles: list[str] | None = None

    writing_preference_score: int | None = Field(default=None, ge=0, le=10)
    movement_preference_score: int | None = Field(default=None, ge=0, le=10)
    breathing_preference_score: int | None = Field(default=None, ge=0, le=10)
    social_support_preference_score: int | None = Field(default=None, ge=0, le=10)
    reflection_preference_score: int | None = Field(default=None, ge=0, le=10)
    structure_preference_score: int | None = Field(default=None, ge=0, le=10)

    @field_validator("preferred_coping_styles", "disliked_coping_styles")
    @classmethod
    def validate_coping_styles(cls, values: list[str] | None) -> list[str] | None:
        return _validate_coping_styles(values)


class UserCopingStyleRead(BaseModel):
    user_id: UUID

    preferred_coping_styles: list[str] | None
    disliked_coping_styles: list[str] | None

    writing_preference_score: int
    movement_preference_score: int
    breathing_preference_score: int
    social_support_preference_score: int
    reflection_preference_score: int
    structure_preference_score: int

    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)