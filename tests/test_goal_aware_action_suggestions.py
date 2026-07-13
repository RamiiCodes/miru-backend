STRESS_MANAGEMENT_RELATED_ACTION_CODES = [
    "short_stress_pause",
    "reduce_scope_today",
    "post_work_decompression_note",
    "name_the_looping_thought",
    "choose_one_small_next_step",
    "work_trigger_note",
]
def _calculate_state(client, headers: dict[str, str]) -> None:
    response = client.post(
        "/state/calculate",
        headers=headers,
    )

    assert response.status_code == 200

def _auth_headers(client, email: str = "goal-aware-actions@example.com") -> dict[str, str]:
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


def _create_goal(
    client,
    headers: dict[str, str],
    category: str,
    priority: int = 9,
) -> dict:
    response = client.post(
        "/user-goals",
        json={
            "category": category,
            "title": "Reduce work stress",
            "description": "I want recommendations that help with stress.",
            "priority": priority,
            "time_horizon": "medium_term",
        },
        headers=headers,
    )

    assert response.status_code == 201

    return response.json()


def _create_stress_journal(client, headers: dict[str, str]) -> None:
    response = client.post(
        "/journals",
        json={
            "content": (
                "I am overwhelmed at work. "
                "I keep thinking about deadlines and I cannot calm down."
            ),
        },
        headers=headers,
    )
    _calculate_state(
    client=client,
    headers=headers,
    )

    assert response.status_code == 201


def _create_high_stress_checkin(client, headers: dict[str, str]) -> None:
    response = client.post(
        "/checkins",
        json={
            "mood_score": 5,
            "stress_score": 8,
            "energy_score": 5,
            "sleep_score": 5,
            "social_score": 5,
        },
        headers=headers,
    )

    assert response.status_code == 201


def test_active_goal_boosts_matching_action_suggestions(client):
    headers = _auth_headers(client)

    _create_goal(
        client=client,
        headers=headers,
        category="stress_management",
        priority=9,
    )

    _create_stress_journal(
        client=client,
        headers=headers,
    )
    _create_high_stress_checkin(
        client=client,
        headers=headers,
    )
    _calculate_state(
    client=client,
    headers=headers,
    )


    response = client.post(
        "/actions/generate",
        headers=headers,
    )

    assert response.status_code == 200

    actions = response.json()

    matching_actions = [
        action
        for action in actions
        if action["action_code"] in STRESS_MANAGEMENT_RELATED_ACTION_CODES
    ]

    assert matching_actions

    assert any(
        action["priority"] == "high"
        and action["confidence"] >= 0.82
        for action in matching_actions
    )


def test_paused_goal_does_not_break_action_generation(client):
    headers = _auth_headers(client, email="paused-goal-aware-actions@example.com")

    goal = _create_goal(
        client=client,
        headers=headers,
        category="stress_management",
        priority=9,
    )

    pause_response = client.patch(
        f"/user-goals/{goal['id']}",
        json={
            "status": "paused",
        },
        headers=headers,
    )

    assert pause_response.status_code == 200

    _create_stress_journal(
        client=client,
        headers=headers,
    )

    _calculate_state(
        client=client,
        headers=headers,
    )

    response = client.post(
        "/actions/generate",
        headers=headers,
    )

    assert response.status_code == 200
    assert isinstance(response.json(), list)
