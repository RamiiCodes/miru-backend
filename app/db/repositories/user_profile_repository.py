from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.orm import Session

from app.db.models.user_profile import UserProfile


def get_user_profile_by_user_id(
    db: Session,
    user_id: UUID,
) -> UserProfile | None:
    return (
        db.query(UserProfile)
        .filter(UserProfile.user_id == user_id)
        .first()
    )


def upsert_user_profile(
    db: Session,
    user_id: UUID,
    display_name: str | None = None,
    birth_year: int | None = None,
    country: str | None = None,
    gender: str | None = None,
    living_situation: str | None = None,
    relationship_status: str | None = None,
    work_status: str | None = None,
    main_life_context: list[str] | None = None,
    interests: list[str] | None = None,
    preferred_reflection_style: str | None = None,
    onboarding_completed: bool | None = None,
) -> UserProfile:
    profile = get_user_profile_by_user_id(
        db=db,
        user_id=user_id,
    )

    if profile is None:
        profile = UserProfile(user_id=user_id)

    if display_name is not None:
        profile.display_name = display_name

    if birth_year is not None:
        profile.birth_year = birth_year

    if country is not None:
        profile.country = country

    if gender is not None:
        profile.gender = gender

    if living_situation is not None:
        profile.living_situation = living_situation

    if relationship_status is not None:
        profile.relationship_status = relationship_status

    if work_status is not None:
        profile.work_status = work_status

    if main_life_context is not None:
        profile.main_life_context = main_life_context

    if interests is not None:
        profile.interests = interests

    if preferred_reflection_style is not None:
        profile.preferred_reflection_style = preferred_reflection_style

    if onboarding_completed is not None:
        profile.onboarding_completed = onboarding_completed

    profile.updated_at = datetime.now(timezone.utc)

    db.add(profile)
    db.commit()
    db.refresh(profile)

    return profile