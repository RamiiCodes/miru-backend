from sqlalchemy.orm import Session

from app.db.models.structured_checkin import StructuredCheckin
from app.db.repositories.signal_catalog_repository import get_signal_by_code
from app.db.repositories.user_signal_repository import (
    create_user_signal,
    get_user_signal_by_source,
)


CHECKIN_SIGNAL_MAPPING = {
    "mood_score": "mood_level",
    "stress_score": "stress_level",
    "energy_score": "energy_level",
    "sleep_score": "sleep_quality",
    "social_score": "social_connection",
}


def normalize_checkin_score(score: int) -> float:
    return round(score / 10, 2)


def create_user_signals_from_checkin(
    db: Session,
    checkin: StructuredCheckin,
) -> None:
    for checkin_field, signal_code in CHECKIN_SIGNAL_MAPPING.items():
        signal = get_signal_by_code(db, signal_code)

        if signal is None:
            raise ValueError(f"Signal not found in catalog: {signal_code}")

        existing_signal = get_user_signal_by_source(
            db=db,
            source_type="structured_checkin",
            source_id=checkin.id,
            signal_id=signal.id,
        )

        if existing_signal:
            continue

        raw_score = getattr(checkin, checkin_field)
        normalized_value = normalize_checkin_score(raw_score)

        create_user_signal(
            db=db,
            user_id=checkin.user_id,
            signal_id=signal.id,
            value=normalized_value,
            confidence=0.95,
            source_type="structured_checkin",
            source_id=checkin.id,
            recorded_at=checkin.created_at,
        )