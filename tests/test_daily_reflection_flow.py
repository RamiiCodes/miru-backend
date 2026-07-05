def _auth_headers(client, email: str = "daily-reflection@example.com") -> dict[str, str]:
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


def _create_checkin(client, headers: dict[str, str]) -> None:
    response = client.post(
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

    assert response.status_code == 201


def _create_journal(client, headers: dict[str, str]) -> None:
    response = client.post(
        "/journals",
        json={
            "content": (
                "I can't stop thinking about work. "
                "I feel like I failed again and I am not good enough."
            ),
        },
        headers=headers,
    )

    assert response.status_code == 201


def test_generate_daily_reflection_from_existing_state_insights_and_actions(client):
    headers = _auth_headers(client)

    _create_checkin(client, headers)
    _create_journal(client, headers)

    insights_response = client.post(
        "/insights/generate",
        headers=headers,
    )

    assert insights_response.status_code == 200
    assert len(insights_response.json()) >= 1

    actions_response = client.post(
        "/actions/generate",
        headers=headers,
    )

    assert actions_response.status_code == 200
    assert len(actions_response.json()) >= 1

    reflection_response = client.post(
        "/daily-reflections/generate",
        headers=headers,
    )

    assert reflection_response.status_code == 200

    reflection = reflection_response.json()

    assert reflection["title"].startswith("Today’s reflection")
    assert reflection["summary"]
    assert reflection["emotional_state_summary"]
    assert reflection["insight_summary"]
    assert reflection["pattern_summary"]
    assert reflection["action_summary"]
    assert "Take a short stress pause. Other options include: Take a short stress pause" not in reflection["action_summary"]
    assert reflection["action_summary"].count("Take a short stress pause") <= 1

    assert "stress" in reflection["focus_areas"]

    assert reflection["source_snapshot_json"]["state_id"] is not None
    assert len(reflection["source_snapshot_json"]["insight_ids"]) >= 1
    assert len(reflection["source_snapshot_json"]["action_ids"]) >= 1

    assert reflection["model_version"] == "daily_reflection_v0_1"


def test_get_latest_daily_reflection(client):
    headers = _auth_headers(client, email="latest-reflection@example.com")

    _create_checkin(client, headers)

    generate_response = client.post(
        "/daily-reflections/generate",
        headers=headers,
    )

    assert generate_response.status_code == 200

    latest_response = client.get(
        "/daily-reflections/latest",
        headers=headers,
    )

    assert latest_response.status_code == 200

    assert latest_response.json()["id"] == generate_response.json()["id"]


def test_generate_daily_reflection_upserts_same_day(client):
    headers = _auth_headers(client, email="upsert-reflection@example.com")

    _create_checkin(client, headers)

    first_response = client.post(
        "/daily-reflections/generate",
        headers=headers,
    )

    assert first_response.status_code == 200

    second_response = client.post(
        "/daily-reflections/generate",
        headers=headers,
    )

    assert second_response.status_code == 200

    assert second_response.json()["id"] == first_response.json()["id"]

    list_response = client.get(
        "/daily-reflections",
        headers=headers,
    )

    assert list_response.status_code == 200
    assert len(list_response.json()) == 1


def test_daily_reflections_require_authentication(client):
    generate_response = client.post("/daily-reflections/generate")
    list_response = client.get("/daily-reflections")
    latest_response = client.get("/daily-reflections/latest")

    assert generate_response.status_code == 401
    assert list_response.status_code == 401
    assert latest_response.status_code == 401


def test_user_only_sees_own_daily_reflections(client):
    user_a_headers = _auth_headers(client, email="reflection-a@example.com")
    user_b_headers = _auth_headers(client, email="reflection-b@example.com")

    _create_checkin(client, user_a_headers)

    user_a_generate_response = client.post(
        "/daily-reflections/generate",
        headers=user_a_headers,
    )

    assert user_a_generate_response.status_code == 200

    user_a_list_response = client.get(
        "/daily-reflections",
        headers=user_a_headers,
    )

    assert user_a_list_response.status_code == 200
    assert len(user_a_list_response.json()) == 1

    user_b_list_response = client.get(
        "/daily-reflections",
        headers=user_b_headers,
    )

    assert user_b_list_response.status_code == 200
    assert user_b_list_response.json() == []

    user_b_latest_response = client.get(
        "/daily-reflections/latest",
        headers=user_b_headers,
    )

    assert user_b_latest_response.status_code == 404