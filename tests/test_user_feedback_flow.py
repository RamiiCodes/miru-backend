def _auth_headers(client, email: str = "feedback@example.com") -> dict[str, str]:
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


def _create_action(client, headers: dict[str, str]) -> dict:
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

    actions_response = client.post(
        "/actions/generate",
        headers=headers,
    )

    assert actions_response.status_code == 200
    assert len(actions_response.json()) >= 1

    return actions_response.json()[0]


def test_create_feedback_for_action_suggestion(client):
    headers = _auth_headers(client)

    action = _create_action(client, headers)

    response = client.post(
        "/feedback",
        json={
            "target_type": "action_suggestion",
            "target_id": action["id"],
            "rating": "useful",
            "comment": "This felt practical.",
        },
        headers=headers,
    )

    assert response.status_code == 200

    feedback = response.json()

    assert feedback["target_type"] == "action_suggestion"
    assert feedback["target_id"] == action["id"]
    assert feedback["rating"] == "useful"
    assert feedback["comment"] == "This felt practical."


def test_list_feedback(client):
    headers = _auth_headers(client, email="list-feedback@example.com")

    action = _create_action(client, headers)

    create_response = client.post(
        "/feedback",
        json={
            "target_type": "action_suggestion",
            "target_id": action["id"],
            "rating": "not_useful",
            "comment": "Not relevant today.",
        },
        headers=headers,
    )

    assert create_response.status_code == 200

    list_response = client.get(
        "/feedback",
        headers=headers,
    )

    assert list_response.status_code == 200

    feedback_list = list_response.json()

    assert len(feedback_list) == 1
    assert feedback_list[0]["rating"] == "not_useful"


def test_feedback_upserts_same_target(client):
    headers = _auth_headers(client, email="upsert-feedback@example.com")

    action = _create_action(client, headers)

    first_response = client.post(
        "/feedback",
        json={
            "target_type": "action_suggestion",
            "target_id": action["id"],
            "rating": "useful",
            "comment": "First comment.",
        },
        headers=headers,
    )

    assert first_response.status_code == 200

    second_response = client.post(
        "/feedback",
        json={
            "target_type": "action_suggestion",
            "target_id": action["id"],
            "rating": "too_vague",
            "comment": "Updated comment.",
        },
        headers=headers,
    )

    assert second_response.status_code == 200

    assert second_response.json()["id"] == first_response.json()["id"]
    assert second_response.json()["rating"] == "too_vague"
    assert second_response.json()["comment"] == "Updated comment."

    list_response = client.get(
        "/feedback",
        headers=headers,
    )

    assert list_response.status_code == 200
    assert len(list_response.json()) == 1


def test_feedback_requires_authentication(client):
    response = client.get("/feedback")

    assert response.status_code == 401

    post_response = client.post(
        "/feedback",
        json={
            "target_type": "action_suggestion",
            "target_id": "00000000-0000-0000-0000-000000000000",
            "rating": "useful",
        },
    )

    assert post_response.status_code == 401


def test_feedback_target_must_belong_to_current_user(client):
    user_a_headers = _auth_headers(client, email="feedback-a@example.com")
    user_b_headers = _auth_headers(client, email="feedback-b@example.com")

    user_a_action = _create_action(client, user_a_headers)

    response = client.post(
        "/feedback",
        json={
            "target_type": "action_suggestion",
            "target_id": user_a_action["id"],
            "rating": "useful",
            "comment": "Trying to rate another user's action.",
        },
        headers=user_b_headers,
    )

    assert response.status_code == 404


def test_feedback_rejects_missing_target(client):
    headers = _auth_headers(client, email="missing-target-feedback@example.com")

    response = client.post(
        "/feedback",
        json={
            "target_type": "action_suggestion",
            "target_id": "00000000-0000-0000-0000-000000000000",
            "rating": "useful",
            "comment": "This target does not exist.",
        },
        headers=headers,
    )

    assert response.status_code == 404