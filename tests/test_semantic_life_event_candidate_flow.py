from app.ai.journal_analyzer import (
    JournalAnalysisResult,
    JournalSemanticFrameResult,
    SemanticEventCandidateResult,
)


class SemanticLifeEventAnalyzer:
    provider = "fake_semantic"
    model_name = "fake_semantic_model_v0"
    prompt_version = "fake_semantic_prompt_v0"

    def analyze(self, content: str) -> JournalAnalysisResult:
        return JournalAnalysisResult(
            detected_signals=[],
            safety_flags=[],
            themes=[],
            life_event_candidates=[],
            emotional_tone="happy, excited",
            summary="The user describes getting engaged.",
            language="en",
            provider=self.provider,
            model_name=self.model_name,
            prompt_version=self.prompt_version,
            raw_output={
                "source": "semantic_life_event_analyzer",
            },
            semantic_frame=JournalSemanticFrameResult(
                emotion_labels=[
                    "happy",
                    "excited",
                ],
                semantic_tags=[
                    "positive_life_event",
                    "relationship_milestone",
                ],
                life_domains=[
                    "relationship",
                    "future_planning",
                ],
                needs=[
                    "celebration",
                    "connection",
                ],
                event_candidates=[
                    SemanticEventCandidateResult(
                        category="relationship",
                        event_type="engagement",
                        title="Got engaged",
                        description="The user got engaged today.",
                        significance=0.9,
                        valence=0.95,
                        confidence=0.95,
                        evidence="I got engaged today",
                        semantic_tags=[
                            "relationship_milestone",
                            "major_transition",
                        ],
                        life_domains=[
                            "relationship",
                            "future_planning",
                        ],
                    )
                ],
                overall_confidence=0.9,
                raw_output={
                    "source": "semantic_frame_with_event_candidate",
                },
            ),
        )


class UnknownCategorySemanticLifeEventAnalyzer:
    provider = "fake_semantic"
    model_name = "fake_semantic_model_v0"
    prompt_version = "fake_semantic_prompt_v0"

    def analyze(self, content: str) -> JournalAnalysisResult:
        return JournalAnalysisResult(
            detected_signals=[],
            safety_flags=[],
            themes=[],
            life_event_candidates=[],
            emotional_tone=None,
            summary="The user describes an unusual important transition.",
            language="en",
            provider=self.provider,
            model_name=self.model_name,
            prompt_version=self.prompt_version,
            raw_output={
                "source": "unknown_category_semantic_analyzer",
            },
            semantic_frame=JournalSemanticFrameResult(
                event_candidates=[
                    SemanticEventCandidateResult(
                        category="identity",
                        event_type="unexpected_identity_shift",
                        title="Unexpected identity shift",
                        description="The user describes an important identity transition.",
                        significance=0.8,
                        valence=0.5,
                        confidence=0.9,
                        evidence="Everything feels different now",
                        semantic_tags=[
                            "identity_transition",
                        ],
                        life_domains=[
                            "identity",
                        ],
                    )
                ],
                overall_confidence=0.9,
                raw_output={
                    "source": "unknown_category_semantic_frame",
                },
            ),
        )


def _auth_headers(
    client,
    email: str,
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


def test_semantic_event_candidate_creates_life_event_without_event_type_hardcoding(
    client,
    monkeypatch,
):
    from app.services import journal_signal_service

    monkeypatch.setattr(
        journal_signal_service,
        "get_journal_analyzer",
        lambda: SemanticLifeEventAnalyzer(),
    )

    headers = _auth_headers(
        client,
        email="semantic-life-event@example.com",
    )

    journal_response = client.post(
        "/journals",
        json={
            "content": "I am so happy, I got engaged today.",
        },
        headers=headers,
    )

    assert journal_response.status_code == 201

    semantic_frames_response = client.get(
        "/journal-semantic-frames",
        headers=headers,
    )

    assert semantic_frames_response.status_code == 200

    semantic_frame = semantic_frames_response.json()[0]

    life_events_response = client.get(
        "/life-events",
        headers=headers,
    )

    assert life_events_response.status_code == 200

    life_events = life_events_response.json()

    assert len(life_events) == 1

    life_event = life_events[0]

    assert life_event["source_type"] == "journal_analysis"
    assert life_event["source_id"] is not None
    assert life_event["source_semantic_frame_id"] == semantic_frame["id"]

    assert life_event["confirmation_status"] == "candidate"

    assert life_event["category"] == "relationship"
    assert life_event["event_type"] == "engagement"
    assert life_event["title"] == "Got engaged"
    assert life_event["description"] == "The user got engaged today."

    assert life_event["significance"] == 0.9
    assert life_event["valence"] == 0.95
    assert life_event["confidence"] == 0.95
    assert life_event["evidence"] == "I got engaged today"

    assert life_event["semantic_tags_json"] == [
        "relationship_milestone",
        "major_transition",
    ]

    assert life_event["life_domains_json"] == [
        "relationship",
        "future_planning",
    ]

    assert life_event["emotional_impact"] is None


def test_semantic_event_candidate_preserves_open_event_type_but_normalizes_unknown_category(
    client,
    monkeypatch,
):
    from app.services import journal_signal_service

    monkeypatch.setattr(
        journal_signal_service,
        "get_journal_analyzer",
        lambda: UnknownCategorySemanticLifeEventAnalyzer(),
    )

    headers = _auth_headers(
        client,
        email="semantic-life-event-unknown-category@example.com",
    )

    journal_response = client.post(
        "/journals",
        json={
            "content": "Everything feels different now.",
        },
        headers=headers,
    )

    assert journal_response.status_code == 201

    life_events_response = client.get(
        "/life-events",
        headers=headers,
    )

    assert life_events_response.status_code == 200

    life_event = life_events_response.json()[0]

    assert life_event["category"] == "other"
    assert life_event["event_type"] == "unexpected_identity_shift"
    assert life_event["title"] == "Unexpected identity shift"
    assert life_event["semantic_tags_json"] == [
        "identity_transition",
    ]
    assert life_event["life_domains_json"] == [
        "identity",
    ]


def test_legacy_life_event_candidate_fallback_still_works(client):
    headers = _auth_headers(
        client,
        email="legacy-life-event-fallback-still-works@example.com",
    )

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

    life_events = life_events_response.json()

    assert len(life_events) == 1
    assert life_events[0]["event_type"] == "bereavement"
    assert life_events[0]["confirmation_status"] == "candidate"