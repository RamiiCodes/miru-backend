def _auth_headers(client, email: str = "user-goal-reasoning@example.com") -> dict[str, str]:
    response = client.post(
        "/auth/register",
        json={
            "email": email,
            "password": "TestPassword123!",
        },
    )

    assert response.status_code == 201

    return {
        "Authorization": f"Bearer {response.json()['access_token']}",
    }


def _create_goal(client, headers: dict[str, str]) -> dict:
    response = client.post(
        "/user-goals",
        json={
            "category": "emotional_awareness",
            "title": "Understand my emotional triggers",
            "description": "I want to notice what usually affects me emotionally.",
            "priority": 8,
            "time_horizon": "long_term",
        },
        headers=headers,
    )

    assert response.status_code == 201

    return response.json()


def test_reflection_response_snapshot_includes_active_user_goals(client):
    headers = _auth_headers(client)

    goal = _create_goal(client, headers)

    response = client.post(
        "/reflection-responses/generate",
        headers=headers,
    )

    assert response.status_code == 200

    reflection = response.json()

    assert reflection["source_snapshot_json"]["user_goals_available"] is True
    assert goal["id"] in reflection["source_snapshot_json"]["user_goal_ids"]


def test_daily_reflection_snapshot_includes_active_user_goals(client):
    headers = _auth_headers(client, email="daily-user-goal-reasoning@example.com")

    goal = _create_goal(client, headers)

    response = client.post(
        "/daily-reflections/generate",
        headers=headers,
    )

    assert response.status_code == 200

    daily_reflection = response.json()

    assert daily_reflection["source_snapshot_json"]["user_goals_available"] is True
    assert goal["id"] in daily_reflection["source_snapshot_json"]["user_goal_ids"]


def test_completed_user_goal_is_not_used_as_reasoning_context(client):
    headers = _auth_headers(client, email="completed-user-goal-reasoning@example.com")

    goal = _create_goal(client, headers)

    complete_response = client.patch(
        f"/user-goals/{goal['id']}/complete",
        headers=headers,
    )

    assert complete_response.status_code == 200

    response = client.post(
        "/reflection-responses/generate",
        headers=headers,
    )

    assert response.status_code == 200

    reflection = response.json()

    assert reflection["source_snapshot_json"]["user_goals_available"] is False
    assert reflection["source_snapshot_json"]["user_goal_ids"] == []


def test_paused_user_goal_is_not_used_as_reasoning_context(client):
    headers = _auth_headers(client, email="paused-user-goal-reasoning@example.com")

    goal = _create_goal(client, headers)

    pause_response = client.patch(
        f"/user-goals/{goal['id']}",
        json={
            "status": "paused",
        },
        headers=headers,
    )

    assert pause_response.status_code == 200

    response = client.post(
        "/reflection-responses/generate",
        headers=headers,
    )

    assert response.status_code == 200

    reflection = response.json()

    assert reflection["source_snapshot_json"]["user_goals_available"] is False
    assert reflection["source_snapshot_json"]["user_goal_ids"] == []