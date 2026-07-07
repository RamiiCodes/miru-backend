def _auth_headers(client, email: str = "safety@example.com") -> dict[str, str]:
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


def _create_safety_journal(client, headers: dict[str, str]) -> dict:
    response = client.post(
        "/journals",
        json={
            "content": (
                "I am in severe distress and I cannot cope tonight."
            ),
        },
        headers=headers,
    )

    assert response.status_code == 201

    return response.json()


def test_safety_event_created_from_journal_safety_flag(client):
    headers = _auth_headers(client)

    journal = _create_safety_journal(client, headers)

    response = client.get(
        "/safety-events",
        headers=headers,
    )

    assert response.status_code == 200

    events = response.json()

    assert len(events) == 1

    event = events[0]

    assert event["flag_type"] == "severe_distress"
    assert event["severity"] == "medium"
    assert event["status"] == "open"
    assert event["source_type"] == "journal_entry"
    assert event["source_id"] == journal["id"]
    assert event["message"] == "A severe distress signal was detected from this entry."


def test_list_open_safety_events(client):
    headers = _auth_headers(client, email="open-safety@example.com")

    _create_safety_journal(client, headers)

    response = client.get(
        "/safety-events/open",
        headers=headers,
    )

    assert response.status_code == 200

    events = response.json()

    assert len(events) == 1
    assert events[0]["status"] == "open"


def test_acknowledge_safety_event(client):
    headers = _auth_headers(client, email="ack-safety@example.com")

    _create_safety_journal(client, headers)

    events_response = client.get(
        "/safety-events/open",
        headers=headers,
    )

    assert events_response.status_code == 200

    safety_event = events_response.json()[0]

    acknowledge_response = client.patch(
        f"/safety-events/{safety_event['id']}/acknowledge",
        headers=headers,
    )

    assert acknowledge_response.status_code == 200

    acknowledged_event = acknowledge_response.json()

    assert acknowledged_event["id"] == safety_event["id"]
    assert acknowledged_event["status"] == "acknowledged"
    assert acknowledged_event["acknowledged_at"] is not None

    open_response = client.get(
        "/safety-events/open",
        headers=headers,
    )

    assert open_response.status_code == 200
    assert open_response.json() == []


def test_safety_events_require_authentication(client):
    list_response = client.get("/safety-events")
    open_response = client.get("/safety-events/open")
    acknowledge_response = client.patch(
        "/safety-events/00000000-0000-0000-0000-000000000000/acknowledge",
    )

    assert list_response.status_code == 401
    assert open_response.status_code == 401
    assert acknowledge_response.status_code == 401


def test_user_only_sees_own_safety_events(client):
    user_a_headers = _auth_headers(client, email="safety-a@example.com")
    user_b_headers = _auth_headers(client, email="safety-b@example.com")

    _create_safety_journal(client, user_a_headers)

    user_a_response = client.get(
        "/safety-events",
        headers=user_a_headers,
    )

    user_b_response = client.get(
        "/safety-events",
        headers=user_b_headers,
    )

    assert user_a_response.status_code == 200
    assert user_b_response.status_code == 200

    assert len(user_a_response.json()) == 1
    assert user_b_response.json() == []


def test_user_cannot_acknowledge_another_users_safety_event(client):
    user_a_headers = _auth_headers(client, email="ack-safety-a@example.com")
    user_b_headers = _auth_headers(client, email="ack-safety-b@example.com")

    _create_safety_journal(client, user_a_headers)

    user_a_events_response = client.get(
        "/safety-events",
        headers=user_a_headers,
    )

    assert user_a_events_response.status_code == 200

    safety_event = user_a_events_response.json()[0]

    response = client.patch(
        f"/safety-events/{safety_event['id']}/acknowledge",
        headers=user_b_headers,
    )

    assert response.status_code == 404


def test_reflection_response_prioritizes_open_safety_event(client):
    headers = _auth_headers(client, email="safety-reflection@example.com")

    _create_safety_journal(client, headers)

    response = client.post(
        "/reflection-responses/generate",
        headers=headers,
    )

    assert response.status_code == 200

    reflection = response.json()

    assert reflection["title"] == "Safety check-in"
    assert reflection["response_type"] == "gentle_checkin"
    assert reflection["suggested_action_id"] is None
    assert "not a crisis service" in reflection["message"]
    assert "severe_distress" in reflection["source_snapshot_json"]["safety_flag_types"]
    assert len(reflection["source_snapshot_json"]["safety_event_ids"]) == 1