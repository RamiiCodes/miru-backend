def _auth_headers(client, email: str = "life-events@example.com") -> dict[str, str]:
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


def _create_grief_journal(client, headers: dict[str, str]) -> dict:
    response = client.post(
        "/journals",
        json={
            "content": "My parents just died. I feel nothing inside me. I am lost.",
        },
        headers=headers,
    )

    assert response.status_code == 201

    return response.json()


def test_journal_life_event_candidate_creates_life_event(client):
    headers = _auth_headers(client)

    _create_grief_journal(client, headers)

    response = client.get(
        "/life-events",
        headers=headers,
    )

    assert response.status_code == 200

    life_events = response.json()

    assert len(life_events) == 1

    life_event = life_events[0]

    assert life_event["source_type"] == "journal_analysis"
    assert life_event["source_id"] is not None

    assert life_event["category"] == "family"
    assert life_event["event_type"] == "bereavement"
    assert life_event["title"] == "Death of someone close"

    assert life_event["confirmation_status"] == "candidate"
    assert life_event["confidence"] == 0.8
    assert life_event["emotional_impact"] is None
    assert life_event["event_date"] is None
    assert life_event["event_date_precision"] == "unknown"
    assert life_event["is_active"] is True


def test_confirm_life_event_with_user_friendly_fields(client):
    headers = _auth_headers(client, email="confirm-life-event@example.com")

    _create_grief_journal(client, headers)

    life_events_response = client.get(
        "/life-events",
        headers=headers,
    )

    life_event = life_events_response.json()[0]

    confirm_response = client.patch(
        f"/life-events/{life_event['id']}/confirm",
        json={
            "confirmation_status": "confirmed",
            "title": "Death of my father",
            "description": "My father passed away recently.",
            "emotional_impact": 9,
            "event_date": "2026-07-12T00:00:00Z",
            "event_date_precision": "day",
        },
        headers=headers,
    )

    assert confirm_response.status_code == 200

    confirmed_event = confirm_response.json()

    assert confirmed_event["confirmation_status"] == "confirmed"
    assert confirmed_event["title"] == "Death of my father"
    assert confirmed_event["description"] == "My father passed away recently."
    assert confirmed_event["emotional_impact"] == 9
    assert confirmed_event["event_date_precision"] == "day"


def test_partially_confirm_life_event(client):
    headers = _auth_headers(client, email="partly-confirm-life-event@example.com")

    _create_grief_journal(client, headers)

    life_event = client.get(
        "/life-events",
        headers=headers,
    ).json()[0]

    response = client.patch(
        f"/life-events/{life_event['id']}/confirm",
        json={
            "confirmation_status": "partially_confirmed",
            "title": "A family loss",
            "emotional_impact": 7,
        },
        headers=headers,
    )

    assert response.status_code == 200

    updated_event = response.json()

    assert updated_event["confirmation_status"] == "partially_confirmed"
    assert updated_event["title"] == "A family loss"
    assert updated_event["emotional_impact"] == 7


def test_dismiss_life_event_candidate(client):
    headers = _auth_headers(client, email="dismiss-life-event@example.com")

    _create_grief_journal(client, headers)

    life_event = client.get(
        "/life-events",
        headers=headers,
    ).json()[0]

    dismiss_response = client.patch(
        f"/life-events/{life_event['id']}/dismiss",
        headers=headers,
    )

    assert dismiss_response.status_code == 200

    dismissed_event = dismiss_response.json()

    assert dismissed_event["confirmation_status"] == "dismissed"
    assert dismissed_event["is_active"] is False

    active_response = client.get(
        "/life-events",
        headers=headers,
    )

    assert active_response.status_code == 200
    assert active_response.json() == []

    include_dismissed_response = client.get(
        "/life-events?include_dismissed=true",
        headers=headers,
    )

    assert include_dismissed_response.status_code == 200
    assert len(include_dismissed_response.json()) == 1


def test_create_manual_life_event(client):
    headers = _auth_headers(client, email="manual-life-event@example.com")

    response = client.post(
        "/life-events",
        json={
            "category": "career",
            "event_type": "job_loss",
            "title": "Lost first engineering job",
            "description": "Company downsized after eight months.",
            "emotional_impact": 9,
            "event_date": "2022-11-15T00:00:00Z",
            "event_date_precision": "day",
        },
        headers=headers,
    )

    assert response.status_code == 201

    life_event = response.json()

    assert life_event["source_type"] == "manual"
    assert life_event["source_id"] is None
    assert life_event["category"] == "career"
    assert life_event["event_type"] == "job_loss"
    assert life_event["title"] == "Lost first engineering job"
    assert life_event["emotional_impact"] == 9
    assert life_event["confirmation_status"] == "confirmed"
    assert life_event["confidence"] == 1.0


def test_life_events_require_authentication(client):
    response = client.get("/life-events")

    assert response.status_code == 401


def test_users_only_see_their_own_life_events(client):
    user_a_headers = _auth_headers(client, email="life-events-a@example.com")
    user_b_headers = _auth_headers(client, email="life-events-b@example.com")

    _create_grief_journal(client, user_a_headers)

    user_a_response = client.get(
        "/life-events",
        headers=user_a_headers,
    )

    user_b_response = client.get(
        "/life-events",
        headers=user_b_headers,
    )

    assert user_a_response.status_code == 200
    assert user_b_response.status_code == 200

    assert len(user_a_response.json()) == 1
    assert user_b_response.json() == []