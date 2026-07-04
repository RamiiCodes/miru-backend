def _register_user(client, email: str) -> tuple[dict[str, str], str]:
    register_response = client.post(
        "/auth/register",
        json={
            "email": email,
            "password": "TestPassword123!",
        },
    )

    assert register_response.status_code == 201

    token = register_response.json()["access_token"]

    headers = {
        "Authorization": f"Bearer {token}",
    }

    me_response = client.get(
        "/auth/me",
        headers=headers,
    )

    assert me_response.status_code == 200

    user_id = me_response.json()["id"]

    return headers, user_id


def _create_checkin(
    client,
    headers: dict[str, str],
    mood_score: int,
    stress_score: int,
    energy_score: int,
    sleep_score: int,
    social_score: int,
) -> dict:
    response = client.post(
        "/checkins",
        json={
            "mood_score": mood_score,
            "stress_score": stress_score,
            "energy_score": energy_score,
            "sleep_score": sleep_score,
            "social_score": social_score,
        },
        headers=headers,
    )

    assert response.status_code == 201

    return response.json()


def _create_strong_journal(client, headers: dict[str, str]) -> dict:
    journal_content = (
        "I can't stop thinking and I feel stuck in my head about work and the project. "
        "I feel like I failed again, I am afraid to fail, and I am not good enough. "
        "It is my fault."
    )

    response = client.post(
        "/journals",
        json={
            "content": journal_content,
        },
        headers=headers,
    )

    assert response.status_code == 201

    return response.json()


def test_users_only_see_their_own_signals_state_and_insights(client):
    user_a_headers, user_a_id = _register_user(
        client,
        email="user-a@example.com",
    )

    user_b_headers, user_b_id = _register_user(
        client,
        email="user-b@example.com",
    )

    assert user_a_id != user_b_id

    # User A creates a full Miru flow.
    _create_checkin(
        client=client,
        headers=user_a_headers,
        mood_score=5,
        stress_score=8,
        energy_score=4,
        sleep_score=5,
        social_score=6,
    )

    _create_strong_journal(
        client=client,
        headers=user_a_headers,
    )

    user_a_insights_response = client.post(
        "/insights/generate",
        headers=user_a_headers,
    )

    assert user_a_insights_response.status_code == 200
    assert len(user_a_insights_response.json()) == 4

    # User B should not see User A signals.
    user_b_signals_response = client.get(
        "/signals",
        headers=user_b_headers,
    )

    assert user_b_signals_response.status_code == 200
    assert user_b_signals_response.json() == []

    # User B should not see User A state.
    user_b_state_response = client.get(
        "/state",
        headers=user_b_headers,
    )

    assert user_b_state_response.status_code == 404

    # User B should not see User A insights.
    user_b_insights_response = client.get(
        "/insights",
        headers=user_b_headers,
    )

    assert user_b_insights_response.status_code == 200
    assert user_b_insights_response.json() == []

    # User B creates their own check-in.
    user_b_checkin = _create_checkin(
        client=client,
        headers=user_b_headers,
        mood_score=8,
        stress_score=2,
        energy_score=7,
        sleep_score=8,
        social_score=7,
    )

    assert user_b_checkin["user_id"] == user_b_id

    user_b_signals_response_after_checkin = client.get(
        "/signals",
        headers=user_b_headers,
    )

    assert user_b_signals_response_after_checkin.status_code == 200

    user_b_signals = user_b_signals_response_after_checkin.json()

    assert len(user_b_signals) == 5

    for signal in user_b_signals:
        assert signal["user_id"] == user_b_id

    user_b_state_response_after_checkin = client.get(
        "/state",
        headers=user_b_headers,
    )

    assert user_b_state_response_after_checkin.status_code == 200

    user_b_state = user_b_state_response_after_checkin.json()

    assert user_b_state["user_id"] == user_b_id
    assert user_b_state["stress_level"] == 0.2
    assert user_b_state["energy_level"] == 0.7
    assert user_b_state["sleep_quality"] == 0.8
    assert user_b_state["social_connection"] == 0.7
    assert user_b_state["emotional_stability"] == 0.8

    # User A should still only see User A data.
    user_a_signals_response = client.get(
        "/signals",
        headers=user_a_headers,
    )

    assert user_a_signals_response.status_code == 200

    user_a_signals = user_a_signals_response.json()

    assert len(user_a_signals) == 9

    for signal in user_a_signals:
        assert signal["user_id"] == user_a_id

    user_a_state_response = client.get(
        "/state",
        headers=user_a_headers,
    )

    assert user_a_state_response.status_code == 200

    user_a_state = user_a_state_response.json()

    assert user_a_state["user_id"] == user_a_id
    assert user_a_state["stress_level"] >= 0.75
    assert user_a_state["motivation"] == 0.3
    assert user_a_state["self_esteem"] == 0.3

    user_a_insights_list_response = client.get(
        "/insights",
        headers=user_a_headers,
    )

    assert user_a_insights_list_response.status_code == 200

    user_a_insights = user_a_insights_list_response.json()

    assert len(user_a_insights) == 4

    for insight in user_a_insights:
        assert insight["user_id"] == user_a_id