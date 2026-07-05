from datetime import date
from uuid import UUID

from sqlalchemy.orm import Session

from app.db.models.pattern_detection import PatternDetection


def get_pattern_detection_by_window(
    db: Session,
    user_id: UUID,
    pattern_code: str,
    window_start_date: date,
    window_end_date: date,
) -> PatternDetection | None:
    return (
        db.query(PatternDetection)
        .filter(
            PatternDetection.user_id == user_id,
            PatternDetection.pattern_code == pattern_code,
            PatternDetection.window_start_date == window_start_date,
            PatternDetection.window_end_date == window_end_date,
        )
        .first()
    )


def create_pattern_detection(
    db: Session,
    user_id: UUID,
    pattern_code: str,
    title: str,
    description: str,
    pattern_type: str,
    severity: str,
    confidence: float,
    evidence_json: dict | None,
    window_start_date: date,
    window_end_date: date,
    detection_window_days: int,
    model_version: str = "pattern_detection_v0_1",
) -> PatternDetection:
    existing_pattern = get_pattern_detection_by_window(
        db=db,
        user_id=user_id,
        pattern_code=pattern_code,
        window_start_date=window_start_date,
        window_end_date=window_end_date,
    )

    if existing_pattern:
        return existing_pattern

    pattern = PatternDetection(
        user_id=user_id,
        pattern_code=pattern_code,
        title=title,
        description=description,
        pattern_type=pattern_type,
        severity=severity,
        confidence=confidence,
        evidence_json=evidence_json,
        window_start_date=window_start_date,
        window_end_date=window_end_date,
        detection_window_days=detection_window_days,
        model_version=model_version,
    )

    db.add(pattern)
    db.commit()
    db.refresh(pattern)

    return pattern


def list_pattern_detections_by_user_id(
    db: Session,
    user_id: UUID,
) -> list[PatternDetection]:
    return (
        db.query(PatternDetection)
        .filter(PatternDetection.user_id == user_id)
        .order_by(PatternDetection.created_at.desc())
        .all()
    )