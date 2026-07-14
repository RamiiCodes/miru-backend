WRITING_COPING_STYLE = {
    "preferred_coping_styles": ["writing", "reflection", "structure"],
    "disliked_coping_styles": ["breathing"],
    "writing_preference_score": 9,
    "movement_preference_score": 4,
    "breathing_preference_score": 1,
    "social_support_preference_score": 5,
    "reflection_preference_score": 8,
    "structure_preference_score": 8,
}


BREATHING_COPING_STYLE = {
    "preferred_coping_styles": ["breathing"],
    "disliked_coping_styles": ["writing"],
    "writing_preference_score": 1,
    "movement_preference_score": 4,
    "breathing_preference_score": 9,
    "social_support_preference_score": 5,
    "reflection_preference_score": 5,
    "structure_preference_score": 5,
}


def _auth_headers(client, email: str = "coping-recommendation@example.com") -> dict[str, str]:
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


def _create_coping_style(
    client,
    headers: dict[str, str],
    payload: dict,
) -> None:
    response = client.put(
        "/user-coping-styles",
        json=payload,
        headers=headers,
    )

    assert response.status_code == 200


def _create_stress_context(client, headers: dict[str, str]) -> None:
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


def test_action_generation_uses_writing_coping_preference(client):
    headers = _auth_headers(client)

    _create_coping_style(client, headers, WRITING_COPING_STYLE)
    _create_stress_context(client, headers)

    response = client.post(
        "/actions/generate",
        headers=headers,
    )

    assert response.status_code == 200

    actions = response.json()

    writing_actions = [
        action
        for action in actions
        if action["action_code"] in [
            "post_work_decompression_note",
            "name_the_looping_thought",
            "work_trigger_note",
            "two_column_thought_check",
        ]
    ]

    breathing_actions = [
        action
        for action in actions
        if action["action_code"] == "short_stress_pause"
    ]

    assert writing_actions

    if breathing_actions:
        assert writing_actions[0]["confidence"] >= breathing_actions[0]["confidence"]


def test_reflection_response_prefers_coping_matched_action(client):
    headers = _auth_headers(
        client,
        email="coping-reflection-response@example.com",
    )

    _create_coping_style(client, headers, WRITING_COPING_STYLE)
    _create_stress_context(client, headers)

    actions_response = client.post(
        "/actions/generate",
        headers=headers,
    )

    assert actions_response.status_code == 200

    reflection_response = client.post(
        "/reflection-responses/generate",
        headers=headers,
    )

    assert reflection_response.status_code == 200

    reflection = reflection_response.json()

    assert reflection["suggested_action_id"] is not None
    assert reflection["source_snapshot_json"]["coping_style_available"] is True

    suggested_action_id = reflection["suggested_action_id"]

    suggested_action = next(
        action
        for action in actions_response.json()
        if action["id"] == suggested_action_id
    )

    assert suggested_action["action_code"] != "short_stress_pause"


def test_daily_reflection_snapshot_includes_coping_style(client):
    headers = _auth_headers(
        client,
        email="coping-daily-reflection@example.com",
    )

    _create_coping_style(client, headers, WRITING_COPING_STYLE)
    _create_stress_context(client, headers)

    actions_response = client.post(
        "/actions/generate",
        headers=headers,
    )

    assert actions_response.status_code == 200

    daily_response = client.post(
        "/daily-reflections/generate",
        headers=headers,
    )

    assert daily_response.status_code == 200

    daily_reflection = daily_response.json()

    assert daily_reflection["source_snapshot_json"]["coping_style_available"] is True
