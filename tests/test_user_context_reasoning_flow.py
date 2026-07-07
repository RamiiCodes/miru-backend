USER_CONTEXT = {
    "age_range_min": 30,
    "age_range_max": 35,
    "country": "France",
    "work_situation": "employed",
    "relationship_status": "single",
    "family_support_score": 2,
    "social_connection_score": 3,
    "work_stress_baseline": 8,
}


def _auth_headers(client, email: str = "context-reasoning@example.com") -> dict[str, str]:
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


def _create_profile(client, headers: dict[str, str]) -> None:
    response = client.patch(
        "/profile",
        json={
            "display_name": "Rami",
            "preferred_reflection_style": "direct",
            "onboarding_completed": True,
        },
        headers=headers,
    )

    assert response.status_code == 200


def _create_user_context(client, headers: dict[str, str]) -> None:
    response = client.put(
        "/user-context",
        json=USER_CONTEXT,
        headers=headers,
    )

    assert response.status_code == 200


def _create_reasoning_activity(client, headers: dict[str, str]) -> None:
    checkin_response = client.post(
        "/checkins",
        json={
            "mood_score": 5,
            "stress_score": 8,
            "energy_score": 4,
            "sleep_score": 5,
            "social_score": 6,
        },
        headers=headers,
    )

    assert checkin_response.status_code == 201

    journal_response = client.post(
        "/journals",
        json={
            "content": (
                "I can't stop thinking about work. "
                "I feel like I failed again and I am not good enough."
            ),
        },
        headers=headers,
    )

    assert journal_response.status_code == 201

    insights_response = client.post(
        "/insights/generate",
        headers=headers,
    )

    assert insights_response.status_code == 200

    actions_response = client.post(
        "/actions/generate",
        headers=headers,
    )

    assert actions_response.status_code == 200


def test_reflection_response_uses_user_context_when_available(client):
    headers = _auth_headers(client)

    _create_profile(client, headers)
    _create_user_context(client, headers)
    _create_reasoning_activity(client, headers)

    response = client.post(
        "/reflection-responses/generate",
        headers=headers,
    )

    assert response.status_code == 200

    reflection = response.json()

    assert "Context note:" in reflection["message"]
    assert "usual work stress baseline is high" in reflection["message"]
    assert "Family support is declared as limited" in reflection["message"]
    assert reflection["source_snapshot_json"]["user_context_available"] is True
    assert reflection["source_snapshot_json"]["user_context_user_id"] is not None


def test_daily_reflection_uses_user_context_when_available(client):
    headers = _auth_headers(client, email="daily-context-reasoning@example.com")

    _create_user_context(client, headers)
    _create_reasoning_activity(client, headers)

    response = client.post(
        "/daily-reflections/generate",
        headers=headers,
    )

    assert response.status_code == 200

    daily_reflection = response.json()

    assert "Context note:" in daily_reflection["summary"]
    assert "declared work stress baseline is high" in daily_reflection["summary"]
    assert daily_reflection["source_snapshot_json"]["user_context_available"] is True
    assert daily_reflection["source_snapshot_json"]["user_context_user_id"] is not None