def _auth_headers(client, email: str = "checkin@example.com") -> dict[str, str]:
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


def test_create_checkin_creates_user_signals_and_current_state(client):
    headers = _auth_headers(client)

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

    checkin = checkin_response.json()

    assert checkin["mood_score"] == 5
    assert checkin["stress_score"] == 8
    assert checkin["energy_score"] == 4
    assert checkin["sleep_score"] == 5
    assert checkin["social_score"] == 6
    assert "id" in checkin
    assert "user_id" in checkin

    signals_response = client.get(
        "/signals",
        headers=headers,
    )

    assert signals_response.status_code == 200

    signals = signals_response.json()

    assert len(signals) == 5

    signals_by_code = {
        signal["signal_code"]: signal
        for signal in signals
    }

    assert set(signals_by_code.keys()) == {
        "mood_level",
        "stress_level",
        "energy_level",
        "sleep_quality",
        "social_connection",
    }

    assert signals_by_code["mood_level"]["value"] == 0.5
    assert signals_by_code["stress_level"]["value"] == 0.8
    assert signals_by_code["energy_level"]["value"] == 0.4
    assert signals_by_code["sleep_quality"]["value"] == 0.5
    assert signals_by_code["social_connection"]["value"] == 0.6

    for signal in signals:
        assert signal["confidence"] == 0.95
        assert signal["source_type"] == "structured_checkin"
        assert signal["source_id"] == checkin["id"]

    state_response = client.get(
        "/state",
        headers=headers,
    )

    assert state_response.status_code == 200

    state = state_response.json()

    assert state["user_id"] == checkin["user_id"]
    assert state["stress_level"] == 0.8
    assert state["energy_level"] == 0.4
    assert state["sleep_quality"] == 0.5
    assert state["social_connection"] == 0.6
    assert state["emotional_stability"] == 0.5

    assert state["motivation"] is None
    assert state["self_esteem"] is None
    assert state["physical_activity"] is None
    assert state["eating_habits"] is None

    assert state["confidence"] == 0.95
    assert state["model_version"].startswith("current_emotional_state_v0_")


def test_checkin_requires_authentication(client):
    response = client.post(
        "/checkins",
        json={
            "mood_score": 5,
            "stress_score": 8,
            "energy_score": 4,
            "sleep_score": 5,
            "social_score": 6,
        },
    )

    assert response.status_code == 401