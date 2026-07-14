from app.ai.journal_analyzer import (
    JournalAnalysisResult,
    JournalSemanticFrameResult,
    SemanticDimensionResult,
)


class FakeSemanticAnalyzer:
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
            summary="The user describes a positive relationship milestone.",
            language="en",
            provider=self.provider,
            model_name=self.model_name,
            prompt_version=self.prompt_version,
            raw_output={
                "source": "fake_semantic_analyzer",
            },
            semantic_frame=JournalSemanticFrameResult(
                core_dimensions={
                    "valence": SemanticDimensionResult(
                        value=0.95,
                        confidence=0.95,
                        evidence="I am so happy",
                        reason="The user directly says they are happy.",
                    ),
                    "arousal": SemanticDimensionResult(
                        value=0.75,
                        confidence=0.8,
                        evidence="so happy",
                        reason="The expression suggests activated emotion.",
                    ),
                    "social_connection": SemanticDimensionResult(
                        value=0.95,
                        confidence=0.9,
                        evidence="I got engaged today",
                        reason="Engagement is a relationship milestone.",
                    ),
                    "threat": SemanticDimensionResult(
                        value=0.05,
                        confidence=0.7,
                        evidence=None,
                        reason="No threat is expressed.",
                    ),
                },
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
                overall_confidence=0.9,
                raw_output={
                    "source": "fake_direct_semantic_frame",
                },
            ),
        )


def _auth_headers(
    client,
    email: str = "semantic-signal-bridge@example.com",
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


def test_semantic_frame_core_dimensions_create_user_signals(client, monkeypatch):
    from app.services import journal_signal_service

    monkeypatch.setattr(
        journal_signal_service,
        "get_journal_analyzer",
        lambda: FakeSemanticAnalyzer(),
    )

    headers = _auth_headers(client)

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

    semantic_frames = semantic_frames_response.json()

    assert len(semantic_frames) == 1

    semantic_frame = semantic_frames[0]

    assert semantic_frame["core_dimensions_json"]["valence"]["value"] == 0.95
    assert semantic_frame["core_dimensions_json"]["arousal"]["value"] == 0.75
    assert semantic_frame["core_dimensions_json"]["social_connection"]["value"] == 0.95
    assert semantic_frame["core_dimensions_json"]["threat"]["value"] == 0.05

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

    assert signals_by_code["semantic_valence"]["value"] == 0.95
    assert signals_by_code["semantic_valence"]["confidence"] == 0.95
    assert signals_by_code["semantic_valence"]["source_type"] == (
        "journal_semantic_frame"
    )
    assert signals_by_code["semantic_valence"]["source_id"] == semantic_frame["id"]

    assert signals_by_code["semantic_arousal"]["value"] == 0.75
    assert signals_by_code["semantic_social_connection"]["value"] == 0.95
    assert signals_by_code["semantic_threat"]["value"] == 0.05


def test_semantic_bridge_does_not_create_signals_for_null_dimensions(
    client,
    monkeypatch,
):
    from app.services import journal_signal_service

    class EmptySemanticAnalyzer(FakeSemanticAnalyzer):
        def analyze(self, content: str) -> JournalAnalysisResult:
            return JournalAnalysisResult(
                detected_signals=[],
                safety_flags=[],
                themes=[],
                life_event_candidates=[],
                emotional_tone=None,
                summary=None,
                language="en",
                provider=self.provider,
                model_name=self.model_name,
                prompt_version=self.prompt_version,
                raw_output={
                    "source": "empty_semantic_analyzer",
                },
                semantic_frame=JournalSemanticFrameResult(
                    core_dimensions={},
                    raw_output={
                        "source": "empty_semantic_frame",
                    },
                ),
            )

    monkeypatch.setattr(
        journal_signal_service,
        "get_journal_analyzer",
        lambda: EmptySemanticAnalyzer(),
    )

    headers = _auth_headers(
        client,
        email="empty-semantic-signal-bridge@example.com",
    )

    journal_response = client.post(
        "/journals",
        json={
            "content": "I wrote something neutral.",
        },
        headers=headers,
    )

    assert journal_response.status_code == 201

    signals_response = client.get(
        "/signals",
        headers=headers,
    )

    assert signals_response.status_code == 200

    signals = signals_response.json()

    semantic_signal_codes = {
        "semantic_valence",
        "semantic_arousal",
        "semantic_threat",
        "semantic_control",
        "semantic_social_connection",
        "semantic_uncertainty",
        "semantic_self_evaluation",
        "semantic_energy",
    }

    assert all(
        signal["signal_code"] not in semantic_signal_codes
        for signal in signals
    )