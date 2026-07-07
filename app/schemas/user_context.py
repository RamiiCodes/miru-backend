from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


class UserContextUpsert(BaseModel):
    age_range_min: int = Field(ge=13, le=120)
    age_range_max: int = Field(ge=13, le=120)

    country: str = Field(min_length=1, max_length=100)

    work_situation: str = Field(min_length=1, max_length=50)
    relationship_status: str = Field(min_length=1, max_length=50)

    family_support_score: int = Field(ge=0, le=10)
    social_connection_score: int = Field(ge=0, le=10)
    work_stress_baseline: int = Field(ge=0, le=10)

    @model_validator(mode="after")
    def validate_age_range(self):
        if self.age_range_min > self.age_range_max:
            raise ValueError("age_range_min must be lower than or equal to age_range_max.")

        return self


class UserContextUpdate(BaseModel):
    age_range_min: int | None = Field(default=None, ge=13, le=120)
    age_range_max: int | None = Field(default=None, ge=13, le=120)

    country: str | None = Field(default=None, min_length=1, max_length=100)

    work_situation: str | None = Field(default=None, min_length=1, max_length=50)
    relationship_status: str | None = Field(default=None, min_length=1, max_length=50)

    family_support_score: int | None = Field(default=None, ge=0, le=10)
    social_connection_score: int | None = Field(default=None, ge=0, le=10)
    work_stress_baseline: int | None = Field(default=None, ge=0, le=10)

    @model_validator(mode="after")
    def validate_age_range_when_both_present(self):
        if (
            self.age_range_min is not None
            and self.age_range_max is not None
            and self.age_range_min > self.age_range_max
        ):
            raise ValueError("age_range_min must be lower than or equal to age_range_max.")

        return self


class UserContextRead(BaseModel):
    user_id: UUID

    age_range_min: int
    age_range_max: int

    country: str

    work_situation: str
    relationship_status: str

    family_support_score: int
    social_connection_score: int
    work_stress_baseline: int

    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)