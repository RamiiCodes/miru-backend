def _auth_headers(client, email: str = "life-event-reasoning@example.com") -> dict[str, str]:
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


def _create_life_event(client, headers: dict[str, str]) -> dict:
    response = client.post(
        "/life-events",
        json={
            "category": "family",
            "event_type": "bereavement",
            "title": "Death of my father",
            "description": "My father passed away recently.",
            "emotional_impact": 9,
            "event_date": "2026-07-12T00:00:00Z",
            "event_date_precision": "day",
        },
        headers=headers,
    )

    assert response.status_code == 201

    return response.json()


def test_reflection_response_includes_confirmed_life_event_context(client):
    headers = _auth_headers(client)

    life_event = _create_life_event(client, headers)

    response = client.post(
        "/reflection-responses/generate",
        headers=headers,
    )

    assert response.status_code == 200

    reflection = response.json()

    assert reflection["source_snapshot_json"]["life_events_available"] is True
    assert life_event["id"] in reflection["source_snapshot_json"]["life_event_ids"]


def test_daily_reflection_snapshot_includes_life_events(client):
    headers = _auth_headers(client, email="daily-life-event-reasoning@example.com")

    life_event = _create_life_event(client, headers)

    response = client.post(
        "/daily-reflections/generate",
        headers=headers,
    )

    assert response.status_code == 200

    daily_reflection = response.json()

    assert daily_reflection["source_snapshot_json"]["life_events_available"] is True
    assert life_event["id"] in daily_reflection["source_snapshot_json"]["life_event_ids"]


def test_candidate_life_event_is_not_used_as_reasoning_context(client):
    headers = _auth_headers(client, email="candidate-life-event-reasoning@example.com")

    journal_response = client.post(
        "/journals",
        json={
            "content": "My parents just died. I feel nothing inside me. I am lost.",
        },
        headers=headers,
    )

    assert journal_response.status_code == 201

    life_events_response = client.get(
        "/life-events",
        headers=headers,
    )

    assert life_events_response.status_code == 200
    assert len(life_events_response.json()) == 1
    assert life_events_response.json()[0]["confirmation_status"] == "candidate"

    reflection_response = client.post(
        "/reflection-responses/generate",
        headers=headers,
    )

    assert reflection_response.status_code == 200

    reflection = reflection_response.json()

    assert reflection["source_snapshot_json"]["life_events_available"] is False
    assert reflection["source_snapshot_json"]["life_event_ids"] == []


def test_partially_confirmed_life_event_is_used_as_reasoning_context(client):
    headers = _auth_headers(client, email="partial-life-event-reasoning@example.com")

    journal_response = client.post(
        "/journals",
        json={
            "content": "My parents just died. I feel nothing inside me. I am lost.",
        },
        headers=headers,
    )

    assert journal_response.status_code == 201

    life_event = client.get(
        "/life-events",
        headers=headers,
    ).json()[0]

    confirm_response = client.patch(
        f"/life-events/{life_event['id']}/confirm",
        json={
            "confirmation_status": "partially_confirmed",
            "title": "A family loss",
            "emotional_impact": 8,
        },
        headers=headers,
    )

    assert confirm_response.status_code == 200

    reflection_response = client.post(
        "/reflection-responses/generate",
        headers=headers,
    )

    assert reflection_response.status_code == 200

    reflection = reflection_response.json()

    assert reflection["source_snapshot_json"]["life_events_available"] is True
    assert life_event["id"] in reflection["source_snapshot_json"]["life_event_ids"]