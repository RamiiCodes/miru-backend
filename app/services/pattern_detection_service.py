from datetime import datetime, time, timedelta, timezone
from uuid import UUID

from sqlalchemy.orm import Session

from app.db.models.pattern_detection import PatternDetection
from app.db.models.signal_catalog import SignalCatalog
from app.db.models.user_signal import UserSignal
from app.db.repositories.pattern_detection_repository import create_pattern_detection


def _clamp(value: float) -> float:
    return round(max(0.0, min(1.0, value)), 2)


def _build_day_signal_values(
    db: Session,
    user_id: UUID,
    window_start_datetime: datetime,
    window_end_datetime: datetime,
) -> dict[str, dict[str, float]]:
    rows = (
        db.query(UserSignal, SignalCatalog.code)
        .join(SignalCatalog, UserSignal.signal_id == SignalCatalog.id)
        .filter(
            UserSignal.user_id == user_id,
            UserSignal.recorded_at >= window_start_datetime,
            UserSignal.recorded_at < window_end_datetime,
        )
        .order_by(UserSignal.recorded_at.asc())
        .all()
    )

    day_values: dict[str, dict[str, float]] = {}

    for user_signal, signal_code in rows:
        day_key = user_signal.recorded_at.date().isoformat()

        if day_key not in day_values:
            day_values[day_key] = {}

        current_value = day_values[day_key].get(signal_code)

        # For V0.1, keep the strongest signal value per day.
        if current_value is None or user_signal.value > current_value:
            day_values[day_key][signal_code] = user_signal.value

    return day_values


def _matching_days_for_signal(
    day_values: dict[str, dict[str, float]],
    signal_code: str,
    threshold: float,
) -> list[dict]:
    matching_days = []

    for day, signals in day_values.items():
        value = signals.get(signal_code)

        if value is not None and value >= threshold:
            matching_days.append(
                {
                    "date": day,
                    "signals": {
                        signal_code: value,
                    },
                }
            )

    return matching_days


def _matching_days_for_combination(
    day_values: dict[str, dict[str, float]],
    required_signals: dict[str, float],
) -> list[dict]:
    matching_days = []

    for day, signals in day_values.items():
        matched_signals = {}

        for signal_code, threshold in required_signals.items():
            value = signals.get(signal_code)

            if value is None or value < threshold:
                matched_signals = {}
                break

            matched_signals[signal_code] = value

        if matched_signals:
            matching_days.append(
                {
                    "date": day,
                    "signals": matched_signals,
                }
            )

    return matching_days


def _average_signal_value(
    matching_days: list[dict],
    signal_code: str,
) -> float:
    values = [
        day["signals"][signal_code]
        for day in matching_days
        if signal_code in day["signals"]
    ]

    if not values:
        return 0.0

    return _clamp(sum(values) / len(values))


def detect_patterns_for_user(
    db: Session,
    user_id: UUID,
    window_days: int = 14,
) -> list[PatternDetection]:
    today = datetime.now(timezone.utc).date()

    window_start_date = today - timedelta(days=window_days - 1)
    window_end_date = today

    window_start_datetime = datetime.combine(
        window_start_date,
        time.min,
        tzinfo=timezone.utc,
    )

    # Exclusive upper bound: tomorrow at 00:00.
    window_end_datetime = datetime.combine(
        window_end_date + timedelta(days=1),
        time.min,
        tzinfo=timezone.utc,
    )

    day_values = _build_day_signal_values(
        db=db,
        user_id=user_id,
        window_start_datetime=window_start_datetime,
        window_end_datetime=window_end_datetime,
    )

    patterns_to_create: list[dict] = []

    work_stress_days = _matching_days_for_combination(
        day_values=day_values,
        required_signals={
            "stress_level": 0.7,
            "work_sensitivity": 0.4,
        },
    )

    if len(work_stress_days) >= 2:
        average_stress = _average_signal_value(
            matching_days=work_stress_days,
            signal_code="stress_level",
        )

        patterns_to_create.append(
            {
                "pattern_code": "repeated_work_stress",
                "title": "Work-related stress appears repeatedly",
                "description": (
                    "Across multiple days, your signals show elevated stress together "
                    "with work-related context. This may indicate that work situations "
                    "are repeatedly influencing your stress level."
                ),
                "pattern_type": "contextual_pattern",
                "severity": "high" if average_stress >= 0.85 else "medium",
                "confidence": 0.72,
                "evidence_json": {
                    "matching_days": work_stress_days,
                    "rule": "stress_level >= 0.7 and work_sensitivity >= 0.4 on at least 2 days",
                },
            }
        )

    rumination_days = _matching_days_for_signal(
        day_values=day_values,
        signal_code="rumination_tendency",
        threshold=0.5,
    )

    if len(rumination_days) >= 2:
        patterns_to_create.append(
            {
                "pattern_code": "repeated_rumination",
                "title": "Rumination appears repeatedly",
                "description": (
                    "Your recent journal-derived signals suggest repetitive thinking "
                    "on multiple days. This may be a recurring cognitive pattern."
                ),
                "pattern_type": "cognitive_pattern",
                "severity": "high" if len(rumination_days) >= 3 else "medium",
                "confidence": 0.68,
                "evidence_json": {
                    "matching_days": rumination_days,
                    "rule": "rumination_tendency >= 0.5 on at least 2 days",
                },
            }
        )

    self_criticism_days = _matching_days_for_signal(
        day_values=day_values,
        signal_code="self_criticism",
        threshold=0.5,
    )

    if len(self_criticism_days) >= 2:
        patterns_to_create.append(
            {
                "pattern_code": "repeated_self_criticism",
                "title": "Self-critical language appears repeatedly",
                "description": (
                    "Your recent signals suggest self-critical thoughts on multiple "
                    "days. Miru will track whether this becomes a recurring pattern."
                ),
                "pattern_type": "self_perception",
                "severity": "medium",
                "confidence": 0.66,
                "evidence_json": {
                    "matching_days": self_criticism_days,
                    "rule": "self_criticism >= 0.5 on at least 2 days",
                },
            }
        )

    sleep_stress_days = _matching_days_for_combination(
        day_values=day_values,
        required_signals={
            "sleep_quality": 0.0,
            "stress_level": 0.7,
        },
    )

    sleep_stress_days = [
        day
        for day in sleep_stress_days
        if day["signals"].get("sleep_quality") is not None
        and day["signals"]["sleep_quality"] <= 0.45
    ]

    if len(sleep_stress_days) >= 2:
        patterns_to_create.append(
            {
                "pattern_code": "low_sleep_high_stress",
                "title": "Lower sleep quality and higher stress appear together",
                "description": (
                    "Across multiple days, lower sleep quality appears together with "
                    "elevated stress. This pattern may be useful to monitor."
                ),
                "pattern_type": "physiological_pattern",
                "severity": "medium",
                "confidence": 0.64,
                "evidence_json": {
                    "matching_days": sleep_stress_days,
                    "rule": "sleep_quality <= 0.45 and stress_level >= 0.7 on at least 2 days",
                },
            }
        )

    created_patterns: list[PatternDetection] = []

    for pattern_data in patterns_to_create:
        created_pattern = create_pattern_detection(
            db=db,
            user_id=user_id,
            pattern_code=pattern_data["pattern_code"],
            title=pattern_data["title"],
            description=pattern_data["description"],
            pattern_type=pattern_data["pattern_type"],
            severity=pattern_data["severity"],
            confidence=pattern_data["confidence"],
            evidence_json=pattern_data["evidence_json"],
            window_start_date=window_start_date,
            window_end_date=window_end_date,
            detection_window_days=window_days,
        )

        created_patterns.append(created_pattern)

    return created_patterns