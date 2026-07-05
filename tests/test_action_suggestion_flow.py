from datetime import datetime, timedelta, timezone

from app.db.repositories.pattern_detection_repository import create_pattern_detection
from app.db.repositories.user_repository import get_user_by_email


def _auth_headers(client, email: str) -> dict[str, str]:
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


def _seed_pattern_detection(
    db_session,
    *,
    user_id,
    pattern_code: str,
    severity: str = "medium",
):
    today = datetime.now(timezone.utc).date()

    return create_pattern_detection(
        db=db_session,
        user_id=user_id,
        pattern_code=pattern_code,
        title=f"Test {pattern_code}",
        description=f"Test source pattern for {pattern_code}.",
        pattern_type="test_pattern",
        severity=severity,
        confidence=0.7,
        evidence_json={
            "matching_days": [
                {
                    "date": (today - timedelta(days=1)).isoformat(),
                    "signals": {},
                },
                {
                    "date": today.isoformat(),
                    "signals": {},
                },
            ],
        },
        window_start_date=today - timedelta(days=1),
        window_end_date=today,
        detection_window_days=2,
    )


def test_action_suggestion_generation_user_isolation_complete_and_dismiss(
    client,
    db_session,
):
    user_a_headers = _auth_headers(client, "actions-a@example.com")
    user_b_headers = _auth_headers(client, "actions-b@example.com")
    user_a = get_user_by_email(db=db_session, email="actions-a@example.com")
    user_b = get_user_by_email(db=db_session, email="actions-b@example.com")

    _seed_pattern_detection(
        db_session,
        user_id=user_a.id,
        pattern_code="repeated_work_stress",
    )
    _seed_pattern_detection(
        db_session,
        user_id=user_a.id,
        pattern_code="repeated_rumination",
    )
    _seed_pattern_detection(
        db_session,
        user_id=user_b.id,
        pattern_code="repeated_self_criticism",
    )

    user_a_generate_response = client.post(
        "/action-suggestions/generate",
        headers=user_a_headers,
    )
    user_b_generate_response = client.post(
        "/action-suggestions/generate",
        headers=user_b_headers,
    )

    assert user_a_generate_response.status_code == 200
    assert user_b_generate_response.status_code == 200

    user_a_actions_by_code = {
        action["action_code"]: action
        for action in user_a_generate_response.json()
    }
    user_b_actions_by_code = {
        action["action_code"]: action
        for action in user_b_generate_response.json()
    }

    assert set(user_a_actions_by_code) == {
        "post_work_decompression_note",
        "name_the_looping_thought",
    }
    assert set(user_b_actions_by_code) == {
        "balanced_self_response",
    }

    for action in user_a_actions_by_code.values():
        assert action["user_id"] == str(user_a.id)
        assert action["source_type"] == "pattern_detection"
        assert action["is_completed"] is False
        assert action["is_dismissed"] is False

    for action in user_b_actions_by_code.values():
        assert action["user_id"] == str(user_b.id)

    user_b_cannot_complete_user_a_response = client.patch(
        (
            "/action-suggestions/"
            f"{user_a_actions_by_code['post_work_decompression_note']['id']}"
            "/complete"
        ),
        headers=user_b_headers,
    )

    assert user_b_cannot_complete_user_a_response.status_code == 404

    user_a_list_response = client.get(
        "/action-suggestions",
        headers=user_a_headers,
    )
    user_b_list_response = client.get(
        "/action-suggestions",
        headers=user_b_headers,
    )

    assert user_a_list_response.status_code == 200
    assert user_b_list_response.status_code == 200

    assert {
        action["action_code"]
        for action in user_a_list_response.json()
    } == set(user_a_actions_by_code)
    assert {
        action["action_code"]
        for action in user_b_list_response.json()
    } == set(user_b_actions_by_code)

    complete_response = client.patch(
        (
            "/action-suggestions/"
            f"{user_a_actions_by_code['post_work_decompression_note']['id']}"
            "/complete"
        ),
        headers=user_a_headers,
    )
    dismiss_response = client.patch(
        (
            "/action-suggestions/"
            f"{user_a_actions_by_code['name_the_looping_thought']['id']}"
            "/dismiss"
        ),
        headers=user_a_headers,
    )

    assert complete_response.status_code == 200
    assert dismiss_response.status_code == 200

    completed_action = complete_response.json()
    dismissed_action = dismiss_response.json()

    assert completed_action["is_completed"] is True
    assert completed_action["completed_at"] is not None
    assert completed_action["is_dismissed"] is False

    assert dismissed_action["is_dismissed"] is True
    assert dismissed_action["dismissed_at"] is not None
    assert dismissed_action["is_completed"] is False

    active_user_a_response = client.get(
        "/action-suggestions",
        headers=user_a_headers,
    )

    assert active_user_a_response.status_code == 200
    assert active_user_a_response.json() == []

    all_user_a_response = client.get(
        "/action-suggestions?include_completed=true&include_dismissed=true",
        headers=user_a_headers,
    )

    assert all_user_a_response.status_code == 200

    all_user_a_actions_by_code = {
        action["action_code"]: action
        for action in all_user_a_response.json()
    }

    assert set(all_user_a_actions_by_code) == set(user_a_actions_by_code)
    assert all_user_a_actions_by_code["post_work_decompression_note"][
        "is_completed"
    ] is True
    assert all_user_a_actions_by_code["name_the_looping_thought"][
        "is_dismissed"
    ] is True
