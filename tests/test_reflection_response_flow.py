def _auth_headers(client, email: str = "reflection-response@example.com") -> dict[str, str]:
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


def _create_profile(client, headers: dict[str, str], style: str = "direct") -> None:
    response = client.patch(
        "/profile",
        json={
            "display_name": "Rami",
            "country": "France",
            "preferred_reflection_style": style,
            "onboarding_completed": True,
        },
        headers=headers,
    )

    assert response.status_code == 200


def _create_context(client, headers: dict[str, str]) -> None:
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


def test_generate_reflection_response_from_current_context(client):
    headers = _auth_headers(client)

    _create_profile(client, headers, style="direct")
    _create_context(client, headers)

    response = client.post(
        "/reflection-responses/generate",
        headers=headers,
    )

    assert response.status_code == 200

    reflection = response.json()

    assert reflection["title"]
    assert reflection["message"]
    assert reflection["tone"] == "direct"
    assert reflection["response_type"] in [
        "supportive_reflection",
        "action_oriented",
        "summary",
        "gentle_checkin",
    ]

    assert reflection["source_type"] == "current_emotional_state"
    assert reflection["source_id"] is not None
    assert reflection["suggested_action_id"] is not None

    assert "not a diagnosis" in reflection["message"]
    assert reflection["source_snapshot_json"]["state_id"] is not None
    assert len(reflection["source_snapshot_json"]["insight_ids"]) >= 1


def test_get_latest_reflection_response(client):
    headers = _auth_headers(client, email="latest-reflection-response@example.com")

    _create_context(client, headers)

    generate_response = client.post(
        "/reflection-responses/generate",
        headers=headers,
    )

    assert generate_response.status_code == 200

    latest_response = client.get(
        "/reflection-responses/latest",
        headers=headers,
    )

    assert latest_response.status_code == 200
    assert latest_response.json()["id"] == generate_response.json()["id"]


def test_list_reflection_responses(client):
    headers = _auth_headers(client, email="list-reflection-response@example.com")

    _create_context(client, headers)

    first_response = client.post(
        "/reflection-responses/generate",
        headers=headers,
    )

    second_response = client.post(
        "/reflection-responses/generate",
        headers=headers,
    )

    assert first_response.status_code == 200
    assert second_response.status_code == 200

    list_response = client.get(
        "/reflection-responses",
        headers=headers,
    )

    assert list_response.status_code == 200
    assert len(list_response.json()) == 2


def test_reflection_response_can_receive_feedback(client):
    headers = _auth_headers(client, email="feedback-reflection-response@example.com")

    _create_context(client, headers)

    reflection_response = client.post(
        "/reflection-responses/generate",
        headers=headers,
    )

    assert reflection_response.status_code == 200

    reflection = reflection_response.json()

    feedback_response = client.post(
        "/feedback",
        json={
            "target_type": "reflection_response",
            "target_id": reflection["id"],
            "rating": "useful",
            "comment": "This felt accurate.",
        },
        headers=headers,
    )

    assert feedback_response.status_code == 200

    feedback = feedback_response.json()

    assert feedback["target_type"] == "reflection_response"
    assert feedback["target_id"] == reflection["id"]
    assert feedback["rating"] == "useful"


def test_reflection_responses_require_authentication(client):
    generate_response = client.post("/reflection-responses/generate")
    list_response = client.get("/reflection-responses")
    latest_response = client.get("/reflection-responses/latest")

    assert generate_response.status_code == 401
    assert list_response.status_code == 401
    assert latest_response.status_code == 401


def test_user_only_sees_own_reflection_responses(client):
    user_a_headers = _auth_headers(client, email="reflection-response-a@example.com")
    user_b_headers = _auth_headers(client, email="reflection-response-b@example.com")

    _create_context(client, user_a_headers)

    user_a_generate_response = client.post(
        "/reflection-responses/generate",
        headers=user_a_headers,
    )

    assert user_a_generate_response.status_code == 200

    user_a_list_response = client.get(
        "/reflection-responses",
        headers=user_a_headers,
    )

    assert user_a_list_response.status_code == 200
    assert len(user_a_list_response.json()) == 1

    user_b_list_response = client.get(
        "/reflection-responses",
        headers=user_b_headers,
    )

    assert user_b_list_response.status_code == 200
    assert user_b_list_response.json() == []

    user_b_latest_response = client.get(
        "/reflection-responses/latest",
        headers=user_b_headers,
    )

    assert user_b_latest_response.status_code == 404