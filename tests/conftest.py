import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Important: set test env before importing app modules
TEST_DATABASE_URL = "postgresql+psycopg://miru:miru_password@localhost:5432/miru_test"

os.environ["DATABASE_URL"] = TEST_DATABASE_URL
os.environ["JWT_SECRET_KEY"] = "miru-test-secret-with-at-least-32-bytes"
os.environ["JWT_ALGORITHM"] = "HS256"
os.environ["ACCESS_TOKEN_EXPIRE_MINUTES"] = "60"
os.environ["JOURNAL_ANALYZER_PROVIDER"] = "keyword"

from app.db import models  # noqa: E402, F401
from app.db.base import Base  # noqa: E402
from app.db.models.signal_catalog import SignalCatalog  # noqa: E402
from app.db.session import get_db  # noqa: E402
from app.main import app  # noqa: E402


engine = create_engine(TEST_DATABASE_URL, pool_pre_ping=True)

TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


TEST_SIGNAL_CATALOG = [
    {
    "code": "semantic_valence",
    "name": "Semantic Valence",
    "domain": "semantic",
    "description": "Generic semantic dimension: negative to positive emotional tone.",
    "is_active": True,
    },
    {
    "code": "semantic_arousal",
    "name": "Semantic Arousal",
    "domain": "semantic",
    "description": "Generic semantic dimension: calm/deactivated to activated/intense.",
    "is_active": True,
    },
    {
    "code": "semantic_threat",
    "name": "Semantic Threat",
    "domain": "semantic",
    "description": "Generic semantic dimension: felt danger, pressure, alarm, or risk.",
    "is_active": True,
    },
    {
    "code": "semantic_control",
    "name": "Semantic Control",
    "domain": "semantic",
    "description": "Generic semantic dimension: sense of agency and ability to act.",
    "is_active": True,
    },
    {
    "code": "semantic_social_connection",
    "name": "Semantic Social Connection",
    "domain": "semantic",
    "description": "Generic semantic dimension: isolation/rejection to connection/support.",
    "is_active": True,
    },
    {
    "code": "semantic_uncertainty",
    "name": "Semantic Uncertainty",
    "domain": "semantic",
    "description": "Generic semantic dimension: clarity/certainty to uncertainty/confusion.",
    "is_active": True,
    },
    {
    "code": "semantic_self_evaluation",
    "name": "Semantic Self Evaluation",
    "domain": "semantic",
    "description": "Generic semantic dimension: self-criticism/shame to self-acceptance/pride.",
    "is_active": True,
    },
    {
    "code": "semantic_energy",
    "name": "Semantic Energy",
    "domain": "semantic",
    "description": "Generic semantic dimension: depleted to energized.",
    "is_active": True,
    },
    {
        "code": "mood_level",
        "name": "Mood Level",
        "domain": "emotional_state",
    },
    {
        "code": "stress_level",
        "name": "Stress Level",
        "domain": "emotional_state",
    },
    {
        "code": "energy_level",
        "name": "Energy Level",
        "domain": "physiological_state",
    },
    {
        "code": "sleep_quality",
        "name": "Sleep Quality",
        "domain": "physiological_state",
    },
    {
        "code": "social_connection",
        "name": "Social Connection",
        "domain": "social_state",
    },
    {
        "code": "rumination_tendency",
        "name": "Rumination Tendency",
        "domain": "cognitive_pattern",
    },
    {
        "code": "self_criticism",
        "name": "Self-Criticism",
        "domain": "cognitive_pattern",
    },
    {
        "code": "fear_of_failure",
        "name": "Fear of Failure",
        "domain": "cognitive_pattern",
    },
    {
        "code": "work_sensitivity",
        "name": "Work Sensitivity",
        "domain": "contextual_pattern",
    },
    {
        "code": "grief_loss",
        "name": "Grief and Loss",
        "domain": "emotional_state",
    },
    {
        "code": "emotional_numbness",
        "name": "Emotional Numbness",
        "domain": "emotional_state",
    },
    {
        "code": "disorientation",
        "name": "Disorientation",
        "domain": "cognitive_pattern",
    },
    {
        "code": "loneliness",
        "name": "Loneliness",
        "domain": "social_state",
    },
    {
        "code": "overwhelm",
        "name": "Overwhelm",
        "domain": "emotional_state",
    },
]


def seed_signal_catalog(db):
    for signal_data in TEST_SIGNAL_CATALOG:
        signal = SignalCatalog(
            code=signal_data["code"],
            name=signal_data["name"],
            domain=signal_data["domain"],
            description=None,
            is_active=True,
        )
        db.add(signal)

    db.commit()


@pytest.fixture()
def db_session():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    db = TestingSessionLocal()

    try:
        seed_signal_catalog(db)
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def client(db_session):
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
