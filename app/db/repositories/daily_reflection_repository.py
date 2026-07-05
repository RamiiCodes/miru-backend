from datetime import date, datetime, timezone
from uuid import UUID

from sqlalchemy.orm import Session

from app.db.models.daily_reflection import DailyReflection


def get_daily_reflection_by_date(
    db: Session,
    user_id: UUID,
    reflection_date: date,
) -> DailyReflection | None:
    return (
        db.query(DailyReflection)
        .filter(
            DailyReflection.user_id == user_id,
            DailyReflection.reflection_date == reflection_date,
        )
        .first()
    )


def get_latest_daily_reflection(
    db: Session,
    user_id: UUID,
) -> DailyReflection | None:
    return (
        db.query(DailyReflection)
        .filter(DailyReflection.user_id == user_id)
        .order_by(DailyReflection.reflection_date.desc(), DailyReflection.created_at.desc())
        .first()
    )


def list_daily_reflections_by_user_id(
    db: Session,
    user_id: UUID,
) -> list[DailyReflection]:
    return (
        db.query(DailyReflection)
        .filter(DailyReflection.user_id == user_id)
        .order_by(DailyReflection.reflection_date.desc())
        .all()
    )


def upsert_daily_reflection(
    db: Session,
    user_id: UUID,
    reflection_date: date,
    title: str,
    summary: str,
    emotional_state_summary: str | None,
    insight_summary: str | None,
    pattern_summary: str | None,
    action_summary: str | None,
    focus_areas: list[str] | None,
    source_snapshot_json: dict | None,
    model_version: str = "daily_reflection_v0_1",
) -> DailyReflection:
    reflection = get_daily_reflection_by_date(
        db=db,
        user_id=user_id,
        reflection_date=reflection_date,
    )

    if reflection is None:
        reflection = DailyReflection(
            user_id=user_id,
            reflection_date=reflection_date,
            title=title,
            summary=summary,
            emotional_state_summary=emotional_state_summary,
            insight_summary=insight_summary,
            pattern_summary=pattern_summary,
            action_summary=action_summary,
            focus_areas=focus_areas,
            source_snapshot_json=source_snapshot_json,
            model_version=model_version,
        )
    else:
        reflection.title = title
        reflection.summary = summary
        reflection.emotional_state_summary = emotional_state_summary
        reflection.insight_summary = insight_summary
        reflection.pattern_summary = pattern_summary
        reflection.action_summary = action_summary
        reflection.focus_areas = focus_areas
        reflection.source_snapshot_json = source_snapshot_json
        reflection.model_version = model_version
        reflection.updated_at = datetime.now(timezone.utc)

    db.add(reflection)
    db.commit()
    db.refresh(reflection)

    return reflection