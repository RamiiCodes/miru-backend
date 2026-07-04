def _auth_headers(client, email: str = "journal@example.com") -> dict[str, str]:
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


def test_create_journal_creates_cognitive_signals_and_updates_state(client):
    headers = _auth_headers(client)

    journal_content = (
        "I can't stop thinking and I feel stuck in my head about work and the project. "
        "I feel like I failed again, I am afraid to fail, and I am not good enough. "
        "It is my fault."
    )

    journal_response = client.post(
        "/journals",
        json={
            "content": journal_content,
        },
        headers=headers,
    )

    assert journal_response.status_code == 201

    journal = journal_response.json()

    assert journal["content"] == journal_content
    assert "id" in journal
    assert "user_id" in journal
    assert "created_at" in journal

    signals_response = client.get(
        "/signals",
        headers=headers,
    )

    assert signals_response.status_code == 200

    signals = signals_response.json()

    signals_by_code = {
        signal["signal_code"]: signal
        for signal in signals
    }

    assert "rumination_tendency" in signals_by_code
    assert "self_criticism" in signals_by_code
    assert "fear_of_failure" in signals_by_code
    assert "work_sensitivity" in signals_by_code

    assert signals_by_code["rumination_tendency"]["value"] == 0.7
    assert signals_by_code["self_criticism"]["value"] == 0.7
    assert signals_by_code["fear_of_failure"]["value"] == 0.7
    assert signals_by_code["work_sensitivity"]["value"] == 0.7

    for signal_code in [
        "rumination_tendency",
        "self_criticism",
        "fear_of_failure",
        "work_sensitivity",
    ]:
        signal = signals_by_code[signal_code]

        assert signal["confidence"] == 0.55
        assert signal["source_type"] == "journal_entry"
        assert signal["source_id"] == journal["id"]

    state_response = client.get(
        "/state",
        headers=headers,
    )

    assert state_response.status_code == 200

    state = state_response.json()

    assert state["user_id"] == journal["user_id"]

    # No check-in was created in this test, so structured state fields stay empty.
    assert state["stress_level"] is None
    assert state["energy_level"] is None
    assert state["sleep_quality"] is None
    assert state["social_connection"] is None
    assert state["emotional_stability"] is None

    # Journal cognitive signals should affect these fields.
    assert state["motivation"] == 0.3
    assert state["self_esteem"] == 0.3

    assert state["confidence"] == 0.55
    assert state["model_version"] == "current_emotional_state_v0_2"


def test_journal_requires_authentication(client):
    response = client.post(
        "/journals",
        json={
            "content": "I can't stop thinking about work.",
        },
    )

    assert response.status_code == 401