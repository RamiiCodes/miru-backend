import uuid
from datetime import datetime, time, timedelta, timezone

from app.db.models.signal_catalog import SignalCatalog
from app.db.models.user_signal import UserSignal
from app.db.repositories.user_repository import get_user_by_email


def _auth_headers(client, email: str = "patterns@example.com") -> dict[str, str]:
    response = client.post(
        "/auth/register",
        json={
            "email": email,
            "password": "TestPassword123!",
        },
    )

    assert response.status_code == 201

    token = response.json()["access_token"]

    return {
        "Authorization": f"Bearer {token}",
    }


def _get_signal_catalog_by_code(db_session) -> dict[str, SignalCatalog]:
    signals = db_session.query(SignalCatalog).all()

    return {
        signal.code: signal
        for signal in signals
    }


def _create_user_signal(
    db_session,
    *,
    user_id,
    signal_id,
    value: float,
    recorded_at: datetime,
) -> None:
    db_session.add(
        UserSignal(
            user_id=user_id,
            signal_id=signal_id,
            value=value,
            confidence=0.9,
            source_type="test_seed",
            source_id=uuid.uuid4(),
            recorded_at=recorded_at,
        )
    )


def _seed_work_stress_day(
    db_session,
    *,
    user_id,
    signals_by_code: dict[str, SignalCatalog],
    recorded_at: datetime,
    stress_level: float = 0.8,
    work_sensitivity: float = 0.7,
) -> None:
    _create_user_signal(
        db_session,
        user_id=user_id,
        signal_id=signals_by_code["stress_level"].id,
        value=stress_level,
        recorded_at=recorded_at,
    )
    _create_user_signal(
        db_session,
        user_id=user_id,
        signal_id=signals_by_code["work_sensitivity"].id,
        value=work_sensitivity,
        recorded_at=recorded_at,
    )


def _seed_signal_values(
    db_session,
    *,
    user_id,
    signals_by_code: dict[str, SignalCatalog],
    recorded_at: datetime,
    signal_values: dict[str, float],
) -> None:
    for signal_code, value in signal_values.items():
        _create_user_signal(
            db_session,
            user_id=user_id,
            signal_id=signals_by_code[signal_code].id,
            value=value,
            recorded_at=recorded_at,
        )


def test_detects_repeated_work_stress_over_two_days(client, db_session):
    headers = _auth_headers(client)
    user = get_user_by_email(db=db_session, email="patterns@example.com")
    signals_by_code = _get_signal_catalog_by_code(db_session)
    today = datetime.now(timezone.utc).date()

    _seed_work_stress_day(
        db_session,
        user_id=user.id,
        signals_by_code=signals_by_code,
        recorded_at=datetime.combine(
            today - timedelta(days=1),
            time(hour=9),
            tzinfo=timezone.utc,
        ),
    )
    _seed_work_stress_day(
        db_session,
        user_id=user.id,
        signals_by_code=signals_by_code,
        recorded_at=datetime.combine(
            today,
            time(hour=9),
            tzinfo=timezone.utc,
        ),
    )
    db_session.commit()

    detect_response = client.post(
        "/pattern-detections/detect",
        headers=headers,
    )

    assert detect_response.status_code == 200

    patterns_by_code = {
        pattern["pattern_code"]: pattern
        for pattern in detect_response.json()
    }

    assert "repeated_work_stress" in patterns_by_code

    work_stress_pattern = patterns_by_code["repeated_work_stress"]

    assert work_stress_pattern["title"] == "Work-related stress appears repeatedly"
    assert work_stress_pattern["pattern_type"] == "contextual_pattern"
    assert work_stress_pattern["severity"] == "medium"
    assert work_stress_pattern["confidence"] == 0.72
    assert work_stress_pattern["detection_window_days"] == 14

    matching_days = work_stress_pattern["evidence_json"]["matching_days"]

    assert len(matching_days) == 2
    assert {
        day["date"]
        for day in matching_days
    } == {
        (today - timedelta(days=1)).isoformat(),
        today.isoformat(),
    }

    for matching_day in matching_days:
        assert matching_day["signals"] == {
            "stress_level": 0.8,
            "work_sensitivity": 0.7,
        }

    list_response = client.get(
        "/pattern-detections",
        headers=headers,
    )

    assert list_response.status_code == 200

    persisted_pattern_codes = {
        pattern["pattern_code"]
        for pattern in list_response.json()
    }

    assert "repeated_work_stress" in persisted_pattern_codes


def test_does_not_detect_work_stress_with_only_one_matching_day(client, db_session):
    headers = _auth_headers(client, email="one-day-pattern@example.com")
    user = get_user_by_email(db=db_session, email="one-day-pattern@example.com")
    signals_by_code = _get_signal_catalog_by_code(db_session)
    today = datetime.now(timezone.utc).date()

    _seed_work_stress_day(
        db_session,
        user_id=user.id,
        signals_by_code=signals_by_code,
        recorded_at=datetime.combine(
            today,
            time(hour=9),
            tzinfo=timezone.utc,
        ),
    )
    db_session.commit()

    detect_response = client.post(
        "/pattern-detections/detect",
        headers=headers,
    )

    assert detect_response.status_code == 200
    assert detect_response.json() == []


def test_detects_multiple_pattern_categories_from_coexisting_signals_over_multiple_days(
    client,
    db_session,
):
    headers = _auth_headers(client, email="multi-category-patterns@example.com")
    user = get_user_by_email(
        db=db_session,
        email="multi-category-patterns@example.com",
    )
    signals_by_code = _get_signal_catalog_by_code(db_session)
    today = datetime.now(timezone.utc).date()

    for day_offset in [2, 1, 0]:
        _seed_signal_values(
            db_session,
            user_id=user.id,
            signals_by_code=signals_by_code,
            recorded_at=datetime.combine(
                today - timedelta(days=day_offset),
                time(hour=9),
                tzinfo=timezone.utc,
            ),
            signal_values={
                "stress_level": 0.8,
                "work_sensitivity": 0.7,
                "rumination_tendency": 0.6,
                "self_criticism": 0.6,
                "sleep_quality": 0.3,
            },
        )

    db_session.commit()

    detect_response = client.post(
        "/pattern-detections/detect",
        headers=headers,
    )

    assert detect_response.status_code == 200

    patterns_by_code = {
        pattern["pattern_code"]: pattern
        for pattern in detect_response.json()
    }

    assert set(patterns_by_code) == {
        "repeated_work_stress",
        "repeated_rumination",
        "repeated_self_criticism",
        "low_sleep_high_stress",
    }

    pattern_codes_by_type = {
        pattern["pattern_type"]: pattern["pattern_code"]
        for pattern in patterns_by_code.values()
    }

    assert pattern_codes_by_type == {
        "contextual_pattern": "repeated_work_stress",
        "cognitive_pattern": "repeated_rumination",
        "self_perception": "repeated_self_criticism",
        "physiological_pattern": "low_sleep_high_stress",
    }

    expected_dates = {
        (today - timedelta(days=2)).isoformat(),
        (today - timedelta(days=1)).isoformat(),
        today.isoformat(),
    }

    for pattern in patterns_by_code.values():
        matching_days = pattern["evidence_json"]["matching_days"]

        assert len(matching_days) == 3
        assert {
            day["date"]
            for day in matching_days
        } == expected_dates

    work_stress_signals = patterns_by_code["repeated_work_stress"]["evidence_json"][
        "matching_days"
    ][0]["signals"]
    rumination_signals = patterns_by_code["repeated_rumination"]["evidence_json"][
        "matching_days"
    ][0]["signals"]
    self_criticism_signals = patterns_by_code["repeated_self_criticism"]["evidence_json"][
        "matching_days"
    ][0]["signals"]
    sleep_stress_signals = patterns_by_code["low_sleep_high_stress"]["evidence_json"][
        "matching_days"
    ][0]["signals"]

    assert work_stress_signals == {
        "stress_level": 0.8,
        "work_sensitivity": 0.7,
    }
    assert patterns_by_code["repeated_rumination"]["severity"] == "high"
    assert rumination_signals == {
        "rumination_tendency": 0.6,
    }
    assert self_criticism_signals == {
        "self_criticism": 0.6,
    }
    assert sleep_stress_signals == {
        "sleep_quality": 0.3,
        "stress_level": 0.8,
    }
