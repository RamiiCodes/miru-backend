from app.db.models.signal_catalog import SignalCatalog
from app.db.session import SessionLocal


INITIAL_SIGNALS = [
    {
        "code": "mood_level",
        "name": "Mood Level",
        "description": "User's reported or inferred mood level.",
        "domain": "emotional_state",
    },
    {
        "code": "stress_level",
        "name": "Stress Level",
        "description": "User's reported or inferred stress level.",
        "domain": "emotional_state",
    },
    {
        "code": "energy_level",
        "name": "Energy Level",
        "description": "User's reported or inferred energy level.",
        "domain": "physiological_state",
    },
    {
        "code": "sleep_quality",
        "name": "Sleep Quality",
        "description": "User's reported or inferred sleep quality.",
        "domain": "physiological_state",
    },
    {
        "code": "social_connection",
        "name": "Social Connection",
        "description": "User's reported or inferred sense of social connection.",
        "domain": "social_state",
    },
    {
        "code": "rumination_tendency",
        "name": "Rumination Tendency",
        "description": "Tendency to repeatedly think about the same event or concern.",
        "domain": "cognitive_pattern",
    },
    {
        "code": "self_criticism",
        "name": "Self-Criticism",
        "description": "Presence of harsh self-evaluation or self-blame.",
        "domain": "cognitive_pattern",
    },
    {
        "code": "fear_of_failure",
        "name": "Fear of Failure",
        "description": "Concern that mistakes or outcomes reflect personal failure.",
        "domain": "cognitive_pattern",
    },
    {
        "code": "work_sensitivity",
        "name": "Work Sensitivity",
        "description": "Sensitivity to work-related stressors, pressure, or feedback.",
        "domain": "contextual_pattern",
    },
]


def seed_signal_catalog() -> None:
    db = SessionLocal()

    try:
        for signal_data in INITIAL_SIGNALS:
            existing_signal = (
                db.query(SignalCatalog)
                .filter(SignalCatalog.code == signal_data["code"])
                .first()
            )

            if existing_signal:
                continue

            db.add(SignalCatalog(**signal_data))

        db.commit()
        print("Signal catalog seeded successfully.")

    finally:
        db.close()


if __name__ == "__main__":
    seed_signal_catalog()