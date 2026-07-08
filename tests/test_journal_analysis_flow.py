def _auth_headers(client, email: str = "journal-analysis@example.com") -> dict[str, str]:
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


def _create_journal(
    client,
    headers: dict[str, str],
    content: str,
) -> dict:
    response = client.post(
        "/journals",
        json={
            "content": content,
        },
        headers=headers,
    )

    assert response.status_code == 201

    return response.json()


def test_creating_journal_creates_journal_analysis(client):
    headers = _auth_headers(client)

    journal = _create_journal(
        client=client,
        headers=headers,
        content=(
            "I can't stop thinking about work. "
            "I feel like I failed again and I am not good enough."
        ),
    )

    response = client.get(
        "/journal-analyses",
        headers=headers,
    )

    assert response.status_code == 200

    analyses = response.json()

    assert len(analyses) == 1

    analysis = analyses[0]

    assert analysis["journal_entry_id"] == journal["id"]
    assert analysis["provider"] == "keyword"
    assert analysis["status"] == "success"
    assert analysis["language"] == "en"
    assert analysis["latency_ms"] is not None
    assert analysis["raw_output_json"] is not None


def test_creating_journal_creates_extracted_signals(client):
    headers = _auth_headers(client, email="journal-extracted-signals@example.com")

    _create_journal(
        client=client,
        headers=headers,
        content=(
            "I can't stop thinking about work. "
            "I feel like I failed again and I am not good enough."
        ),
    )

    response = client.get(
        "/journal-analyses",
        headers=headers,
    )

    assert response.status_code == 200

    analyses = response.json()
    analysis = analyses[0]

    extracted_signals = analysis["extracted_signals"]

    signal_codes = {
        signal["signal_code"]
        for signal in extracted_signals
    }

    assert "rumination_tendency" in signal_codes
    assert "self_criticism" in signal_codes
    assert "fear_of_failure" in signal_codes
    assert "work_sensitivity" in signal_codes

    for signal in extracted_signals:
        assert 0 <= signal["value"] <= 1
        assert 0 <= signal["confidence"] <= 1
        assert signal["journal_analysis_id"] == analysis["id"]


def test_extracted_journal_signals_create_user_signals(client):
    headers = _auth_headers(client, email="journal-to-user-signals@example.com")

    _create_journal(
        client=client,
        headers=headers,
        content=(
            "I can't stop thinking about work. "
            "I feel like I failed again and I am not good enough."
        ),
    )

    response = client.get(
        "/signals",
        headers=headers,
    )

    assert response.status_code == 200

    user_signals = response.json()

    signal_codes = {
        signal["signal_code"]
        for signal in user_signals
    }

    assert "rumination_tendency" in signal_codes
    assert "self_criticism" in signal_codes
    assert "fear_of_failure" in signal_codes
    assert "work_sensitivity" in signal_codes

    journal_signals = [
        signal
        for signal in user_signals
        if signal["source_type"] == "journal_extracted_signal"
    ]

    assert len(journal_signals) >= 1


def test_journal_analysis_detects_grief_numbness_and_disorientation(client):
    headers = _auth_headers(client, email="grief-journal-analysis@example.com")

    journal = _create_journal(
        client=client,
        headers=headers,
        content="My parents just died. I feel nothing inside me. I am lost.",
    )

    response = client.get(
        "/journal-analyses",
        headers=headers,
    )

    assert response.status_code == 200

    analyses = response.json()

    assert len(analyses) == 1

    analysis = analyses[0]

    assert analysis["journal_entry_id"] == journal["id"]

    assert "grief" in analysis["themes"]
    assert "emotional_numbness" in analysis["themes"]
    assert "disorientation" in analysis["themes"]

    signal_codes = {
        signal["signal_code"]
        for signal in analysis["extracted_signals"]
    }

    assert "grief_loss" in signal_codes
    assert "emotional_numbness" in signal_codes
    assert "disorientation" in signal_codes

    assert analysis["life_event_candidates_json"]
    assert analysis["life_event_candidates_json"][0]["event_type"] == "bereavement"
    assert analysis["life_event_candidates_json"][0]["severity"] == "high"


def test_journal_analysis_safety_flags_still_create_safety_events(client):
    headers = _auth_headers(client, email="journal-analysis-safety@example.com")

    _create_journal(
        client=client,
        headers=headers,
        content="I am in severe distress and I cannot cope tonight.",
    )

    analyses_response = client.get(
        "/journal-analyses",
        headers=headers,
    )

    assert analyses_response.status_code == 200

    analysis = analyses_response.json()[0]

    assert "severe_distress" in analysis["safety_flags"]

    safety_response = client.get(
        "/safety-events/open",
        headers=headers,
    )

    assert safety_response.status_code == 200

    safety_events = safety_response.json()

    assert len(safety_events) == 1
    assert safety_events[0]["flag_type"] == "severe_distress"
    assert safety_events[0]["source_type"] == "journal_entry"


def test_journal_analyses_require_authentication(client):
    response = client.get("/journal-analyses")

    assert response.status_code == 401


def test_users_only_see_their_own_journal_analyses(client):
    user_a_headers = _auth_headers(client, email="journal-analysis-a@example.com")
    user_b_headers = _auth_headers(client, email="journal-analysis-b@example.com")

    _create_journal(
        client=client,
        headers=user_a_headers,
        content="I can't stop thinking about work.",
    )

    user_a_response = client.get(
        "/journal-analyses",
        headers=user_a_headers,
    )

    user_b_response = client.get(
        "/journal-analyses",
        headers=user_b_headers,
    )

    assert user_a_response.status_code == 200
    assert user_b_response.status_code == 200

    assert len(user_a_response.json()) == 1
    assert user_b_response.json() == []


def test_journal_analysis_raw_output_contains_structured_fields(client):
    headers = _auth_headers(client, email="journal-raw-output@example.com")

    _create_journal(
        client=client,
        headers=headers,
        content="I feel lonely and overwhelmed.",
    )

    response = client.get(
        "/journal-analyses",
        headers=headers,
    )

    assert response.status_code == 200

    analysis = response.json()[0]

    raw_output = analysis["raw_output_json"]

    assert "detected_signals" in raw_output
    assert "themes" in raw_output
    assert "safety_flags" in raw_output
    assert "life_event_candidates" in raw_output