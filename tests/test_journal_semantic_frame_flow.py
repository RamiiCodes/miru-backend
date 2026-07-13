from app.services.semantic_frame_normalizer import CORE_DIMENSION_NAMES


def _auth_headers(
    client,
    email: str = "semantic-frame@example.com",
) -> dict[str, str]:
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


def test_journal_creates_semantic_frame_from_keyword_analysis(client):
    headers = _auth_headers(client)

    journal_response = client.post(
        "/journals",
        json={
            "content": "My parents just died. I feel nothing inside me. I am lost.",
        },
        headers=headers,
    )

    assert journal_response.status_code == 201

    response = client.get(
        "/journal-semantic-frames",
        headers=headers,
    )

    assert response.status_code == 200

    semantic_frames = response.json()

    assert len(semantic_frames) == 1

    semantic_frame = semantic_frames[0]

    assert semantic_frame["provider"] == "keyword"
    assert semantic_frame["model_name"] == "keyword_rules_v0_2"
    assert semantic_frame["prompt_version"] == "journal_signal_extraction_v0_2"

    assert semantic_frame["journal_entry_id"] == journal_response.json()["id"]
    assert semantic_frame["journal_analysis_id"] is not None

    assert "grief" in semantic_frame["semantic_tags_json"]
    assert "emotional_numbness" in semantic_frame["semantic_tags_json"]
    assert "disorientation" in semantic_frame["semantic_tags_json"]

    assert semantic_frame["safety_flags_json"] == []

    assert semantic_frame["event_candidates_json"]
    assert semantic_frame["event_candidates_json"][0]["event_type"] == "bereavement"

    assert semantic_frame["raw_output_json"]["source"] == (
        "legacy_analyzer_compatibility_bridge"
    )

    assert set(semantic_frame["core_dimensions_json"].keys()) == set(
        CORE_DIMENSION_NAMES
    )

    assert semantic_frame["core_dimensions_json"]["valence"] is None
    assert semantic_frame["core_dimensions_json"]["arousal"] is None
    


def test_get_single_journal_semantic_frame(client):
    headers = _auth_headers(
        client,
        email="single-semantic-frame@example.com",
    )

    client.post(
        "/journals",
        json={
            "content": "My parents just died. I feel nothing inside me. I am lost.",
        },
        headers=headers,
    )

    list_response = client.get(
        "/journal-semantic-frames",
        headers=headers,
    )

    semantic_frame_id = list_response.json()[0]["id"]

    get_response = client.get(
        f"/journal-semantic-frames/{semantic_frame_id}",
        headers=headers,
    )

    assert get_response.status_code == 200
    assert get_response.json()["id"] == semantic_frame_id


def test_journal_semantic_frames_require_authentication(client):
    response = client.get("/journal-semantic-frames")

    assert response.status_code == 401


def test_users_only_see_their_own_semantic_frames(client):
    user_a_headers = _auth_headers(
        client,
        email="semantic-frame-a@example.com",
    )

    user_b_headers = _auth_headers(
        client,
        email="semantic-frame-b@example.com",
    )

    client.post(
        "/journals",
        json={
            "content": "My parents just died. I feel nothing inside me. I am lost.",
        },
        headers=user_a_headers,
    )

    user_a_response = client.get(
        "/journal-semantic-frames",
        headers=user_a_headers,
    )

    user_b_response = client.get(
        "/journal-semantic-frames",
        headers=user_b_headers,
    )

    assert user_a_response.status_code == 200
    assert user_b_response.status_code == 200

    assert len(user_a_response.json()) == 1
    assert user_b_response.json() == []


def test_keyword_analyzer_returns_semantic_frame_contract():
    from app.ai.providers.keyword_journal_analyzer import KeywordJournalAnalyzer

    analyzer = KeywordJournalAnalyzer()

    result = analyzer.analyze(
        "My parents just died. I feel nothing inside me. I am lost."
    )

    assert result.semantic_frame is not None
    assert "grief" in result.semantic_frame.semantic_tags
    assert result.semantic_frame.event_candidates
    assert result.semantic_frame.event_candidates[0].event_type == "bereavement"
