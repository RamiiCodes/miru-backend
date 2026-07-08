def _auth_headers(client, email: str = "journal@example.com") -> dict[str, str]:
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
        assert signals_by_code[signal_code]["source_type"] == "journal_extracted_signal"
        assert signals_by_code[signal_code]["source_id"] is not None

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


def test_create_journal_creates_journal_analysis_layer(client):
    headers = _auth_headers(client, email="journal-analysis-layer@example.com")

    journal_content = (
        "I can't stop thinking and I feel stuck in my head about work and the project. "
        "I feel like I failed again, I am afraid to fail, and I am not good enough."
    )

    journal_response = client.post(
        "/journals",
        json={
            "content": journal_content,
        },
        headers=headers,
    )

    assert journal_response.status_code == 201

    analyses_response = client.get(
        "/journal-analyses",
        headers=headers,
    )

    assert analyses_response.status_code == 200

    analyses = analyses_response.json()

    assert len(analyses) == 1

    analysis = analyses[0]

    assert analysis["status"] == "success"
    assert analysis["provider"] == "keyword"
    assert analysis["model_name"] == "keyword_rules_v0_2"
    assert analysis["prompt_version"] == "journal_signal_extraction_v0_2"
    assert analysis["journal_entry_id"] == journal_response.json()["id"]

    extracted_signal_codes = {
        signal["signal_code"]
        for signal in analysis["extracted_signals"]
    }

    assert "rumination_tendency" in extracted_signal_codes
    assert "self_criticism" in extracted_signal_codes
    assert "fear_of_failure" in extracted_signal_codes
    assert "work_sensitivity" in extracted_signal_codes


def test_create_journal_requires_authentication(client):
    response = client.post(
        "/journals",
        json={
            "content": "I can't stop thinking about work.",
        },
    )

    assert response.status_code == 401


def test_user_can_create_multiple_journals(client):
    headers = _auth_headers(client, email="multiple-journals@example.com")

    first_response = client.post(
        "/journals",
        json={
            "content": "I can't stop thinking about work.",
        },
        headers=headers,
    )

    second_response = client.post(
        "/journals",
        json={
            "content": "I feel like I failed again.",
        },
        headers=headers,
    )

    assert first_response.status_code == 201
    assert second_response.status_code == 201

    assert first_response.json()["id"] != second_response.json()["id"]

    analyses_response = client.get(
        "/journal-analyses",
        headers=headers,
    )

    assert analyses_response.status_code == 200
    assert len(analyses_response.json()) == 2


def test_journal_with_grief_creates_broader_analysis_signals(client):
    headers = _auth_headers(client, email="journal-grief-flow@example.com")

    journal_response = client.post(
        "/journals",
        json={
            "content": "My parents just died. I feel nothing inside me. I am lost.",
        },
        headers=headers,
    )

    assert journal_response.status_code == 201

    analyses_response = client.get(
        "/journal-analyses",
        headers=headers,
    )

    assert analyses_response.status_code == 200

    analysis = analyses_response.json()[0]

    assert "grief" in analysis["themes"]
    assert "emotional_numbness" in analysis["themes"]
    assert "disorientation" in analysis["themes"]

    extracted_signal_codes = {
        signal["signal_code"]
        for signal in analysis["extracted_signals"]
    }

    assert "grief_loss" in extracted_signal_codes
    assert "emotional_numbness" in extracted_signal_codes
    assert "disorientation" in extracted_signal_codes

    assert analysis["life_event_candidates_json"]
    assert analysis["life_event_candidates_json"][0]["event_type"] == "bereavement"