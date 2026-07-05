def _auth_headers(client, email: str = "llmrun@example.com") -> dict[str, str]:
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


def test_create_journal_creates_llm_run(client):
    headers = _auth_headers(client)

    journal_content = (
        "I can't stop thinking about work. "
        "I feel like I am not good enough and it is my fault."
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

    llm_runs_response = client.get(
        "/llm-runs",
        headers=headers,
    )

    assert llm_runs_response.status_code == 200

    llm_runs = llm_runs_response.json()

    assert len(llm_runs) == 1

    llm_run = llm_runs[0]

    assert llm_run["source_type"] == "journal_entry"
    assert llm_run["source_id"] == journal["id"]

    assert llm_run["provider"] == "keyword"
    assert llm_run["model_name"] == "keyword_rules_v0_1"
    assert llm_run["prompt_version"] == "journal_signal_extraction_v0_1"

    assert llm_run["input_text"] == journal_content
    assert llm_run["status"] == "success"
    assert llm_run["error_message"] is None
    assert llm_run["latency_ms"] is not None

    output_json = llm_run["output_json"]

    assert output_json["provider"] == "keyword"
    assert output_json["model_name"] == "keyword_rules_v0_1"
    assert output_json["prompt_version"] == "journal_signal_extraction_v0_1"

    detected_signals = output_json["detected_signals"]

    signal_codes = {
        signal["signal_code"]
        for signal in detected_signals
    }

    assert "rumination_tendency" in signal_codes
    assert "self_criticism" in signal_codes
    assert "work_sensitivity" in signal_codes


def test_llm_runs_require_authentication(client):
    response = client.get("/llm-runs")

    assert response.status_code == 401


def test_user_only_sees_own_llm_runs(client):
    user_a_headers = _auth_headers(client, email="llm-user-a@example.com")
    user_b_headers = _auth_headers(client, email="llm-user-b@example.com")

    user_a_journal_response = client.post(
        "/journals",
        json={
            "content": "I can't stop thinking about work.",
        },
        headers=user_a_headers,
    )

    assert user_a_journal_response.status_code == 201

    user_a_llm_runs_response = client.get(
        "/llm-runs",
        headers=user_a_headers,
    )

    assert user_a_llm_runs_response.status_code == 200
    assert len(user_a_llm_runs_response.json()) == 1

    user_b_llm_runs_response = client.get(
        "/llm-runs",
        headers=user_b_headers,
    )

    assert user_b_llm_runs_response.status_code == 200
    assert user_b_llm_runs_response.json() == []