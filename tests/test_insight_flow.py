def _auth_headers(client, email: str = "insight@example.com") -> dict[str, str]:
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


def _create_checkin(client, headers: dict[str, str]) -> dict:
    response = client.post(
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

    assert response.status_code == 201

    return response.json()


def _create_journal(client, headers: dict[str, str]) -> dict:
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


def test_generate_insights_from_state_and_signals(client):
    headers = _auth_headers(client)

    _create_checkin(client, headers)
    _create_journal(client, headers)

    state_response = client.get(
        "/state",
        headers=headers,
    )

    assert state_response.status_code == 200

    state = state_response.json()

    assert state["stress_level"] is not None
    assert state["stress_level"] >= 0.75
    assert state["motivation"] == 0.3
    assert state["self_esteem"] == 0.3

    generate_response = client.post(
        "/insights/generate",
        headers=headers,
    )

    assert generate_response.status_code == 200

    generated_insights = generate_response.json()

    assert len(generated_insights) == 4

    insights_by_rule = {
        insight["rule_code"]: insight
        for insight in generated_insights
    }

    assert "stress_rumination_connection" in insights_by_rule
    assert "self_criticism_self_esteem_connection" in insights_by_rule
    assert "fear_failure_motivation_connection" in insights_by_rule
    assert "work_context_stress_connection" in insights_by_rule

    stress_insight = insights_by_rule["stress_rumination_connection"]

    assert stress_insight["title"] == "Stress may be linked to repetitive thinking"
    assert stress_insight["insight_type"] == "cognitive_pattern"
    assert stress_insight["severity"] in ["medium", "high"]
    assert stress_insight["confidence"] == 0.68
    assert stress_insight["model_version"] == "basic_insight_v0_1"

    self_esteem_insight = insights_by_rule["self_criticism_self_esteem_connection"]

    assert self_esteem_insight["insight_type"] == "self_perception"
    assert self_esteem_insight["severity"] == "medium"
    assert self_esteem_insight["confidence"] == 0.65

    motivation_insight = insights_by_rule["fear_failure_motivation_connection"]

    assert motivation_insight["insight_type"] == "motivation_pattern"
    assert motivation_insight["severity"] == "medium"
    assert motivation_insight["confidence"] == 0.64

    work_insight = insights_by_rule["work_context_stress_connection"]

    assert work_insight["insight_type"] == "contextual_pattern"
    assert work_insight["severity"] == "medium"
    assert work_insight["confidence"] == 0.62

    list_response = client.get(
        "/insights",
        headers=headers,
    )

    assert list_response.status_code == 200

    persisted_insights = list_response.json()

    assert len(persisted_insights) == 4

    persisted_rules = {
        insight["rule_code"]
        for insight in persisted_insights
    }

    assert persisted_rules == {
        "stress_rumination_connection",
        "self_criticism_self_esteem_connection",
        "fear_failure_motivation_connection",
        "work_context_stress_connection",
    }


def test_generate_insights_twice_does_not_duplicate_same_state_rules(client):
    headers = _auth_headers(client, email="duplicate-insight@example.com")

    _create_checkin(client, headers)
    _create_journal(client, headers)

    first_response = client.post(
        "/insights/generate",
        headers=headers,
    )

    assert first_response.status_code == 200
    assert len(first_response.json()) == 4

    second_response = client.post(
        "/insights/generate",
        headers=headers,
    )

    assert second_response.status_code == 200
    assert len(second_response.json()) == 4

    list_response = client.get(
        "/insights",
        headers=headers,
    )

    assert list_response.status_code == 200

    persisted_insights = list_response.json()

    assert len(persisted_insights) == 4

    rule_codes = [
        insight["rule_code"]
        for insight in persisted_insights
    ]

    assert len(rule_codes) == len(set(rule_codes))


def test_insights_require_authentication(client):
    generate_response = client.post("/insights/generate")
    list_response = client.get("/insights")

    assert generate_response.status_code == 401
    assert list_response.status_code == 401