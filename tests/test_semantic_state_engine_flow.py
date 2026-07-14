from app.ai.journal_analyzer import (
    JournalAnalysisResult,
    JournalSemanticFrameResult,
    SemanticDimensionResult,
)


class PositiveSemanticAnalyzer:
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
                "source": "positive_semantic_analyzer",
            },
            semantic_frame=JournalSemanticFrameResult(
                core_dimensions={
                    "valence": SemanticDimensionResult(
                        value=0.95,
                        confidence=0.95,
                        evidence="I am so happy",
                        reason="Strong positive wording.",
                    ),
                    "arousal": SemanticDimensionResult(
                        value=0.75,
                        confidence=0.8,
                        evidence="so happy",
                        reason="Activated positive emotion.",
                    ),
                    "social_connection": SemanticDimensionResult(
                        value=0.95,
                        confidence=0.9,
                        evidence="I got engaged today",
                        reason="Relationship milestone.",
                    ),
                    "threat": SemanticDimensionResult(
                        value=0.05,
                        confidence=0.7,
                        evidence=None,
                        reason="No threat is expressed.",
                    ),
                    "energy": SemanticDimensionResult(
                        value=0.8,
                        confidence=0.75,
                        evidence="so happy",
                        reason="Positive activation suggests energy.",
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
                ],
                needs=[
                    "celebration",
                    "connection",
                ],
                overall_confidence=0.9,
                raw_output={
                    "source": "positive_semantic_frame",
                },
            ),
        )


class ThreatLowControlSemanticAnalyzer:
    provider = "fake_semantic"
    model_name = "fake_semantic_model_v0"
    prompt_version = "fake_semantic_prompt_v0"

    def analyze(self, content: str) -> JournalAnalysisResult:
        return JournalAnalysisResult(
            detected_signals=[],
            safety_flags=[],
            themes=[],
            life_event_candidates=[],
            emotional_tone="pressured, uncertain",
            summary="The user describes pressure and low control.",
            language="en",
            provider=self.provider,
            model_name=self.model_name,
            prompt_version=self.prompt_version,
            raw_output={
                "source": "threat_semantic_analyzer",
            },
            semantic_frame=JournalSemanticFrameResult(
                core_dimensions={
                    "threat": SemanticDimensionResult(
                        value=0.85,
                        confidence=0.9,
                        evidence="I feel under pressure",
                        reason="The user describes pressure.",
                    ),
                    "control": SemanticDimensionResult(
                        value=0.2,
                        confidence=0.85,
                        evidence="I can't do anything",
                        reason="The user describes low agency.",
                    ),
                    "uncertainty": SemanticDimensionResult(
                        value=0.75,
                        confidence=0.8,
                        evidence="I don't know what will happen",
                        reason="The user describes uncertainty.",
                    ),
                    "valence": SemanticDimensionResult(
                        value=0.2,
                        confidence=0.8,
                        evidence="under pressure",
                        reason="Negative emotional tone.",
                    ),
                },
                emotion_labels=[
                    "pressured",
                    "uncertain",
                ],
                semantic_tags=[
                    "low_control",
                    "high_pressure",
                ],
                needs=[
                    "grounding",
                    "clarity",
                ],
                overall_confidence=0.85,
                raw_output={
                    "source": "threat_semantic_frame",
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


def test_positive_semantic_frame_updates_state_without_positive_emotion_hardcoding(
    client,
    monkeypatch,
):
    from app.services import journal_signal_service

    monkeypatch.setattr(
        journal_signal_service,
        "get_journal_analyzer",
        lambda: PositiveSemanticAnalyzer(),
    )

    headers = _auth_headers(
        client,
        email="positive-semantic-state@example.com",
    )

    journal_response = client.post(
        "/journals",
        json={
            "content": "I am so happy, I got engaged today.",
        },
        headers=headers,
    )

    assert journal_response.status_code == 201

    state_response = client.post(
        "/state/calculate",
        headers=headers,
    )

    assert state_response.status_code == 200

    state = state_response.json()

    assert state["emotional_stability"] >= 0.8
    assert state["social_connection"] >= 0.8
    assert state["energy_level"] >= 0.7
    assert state["stress_level"] <= 0.3


def test_threat_and_low_control_update_stress_without_legacy_signal_rules(
    client,
    monkeypatch,
):
    from app.services import journal_signal_service

    monkeypatch.setattr(
        journal_signal_service,
        "get_journal_analyzer",
        lambda: ThreatLowControlSemanticAnalyzer(),
    )

    headers = _auth_headers(
        client,
        email="threat-semantic-state@example.com",
    )

    journal_response = client.post(
        "/journals",
        json={
            "content": (
                "I feel under pressure. I can't do anything. "
                "I don't know what will happen."
            ),
        },
        headers=headers,
    )

    assert journal_response.status_code == 201

    state_response = client.post(
        "/state/calculate",
        headers=headers,
    )

    assert state_response.status_code == 200

    state = state_response.json()

    assert state["stress_level"] >= 0.7
    assert state["emotional_stability"] <= 0.4


def test_legacy_grief_flow_still_updates_state(client):
    headers = _auth_headers(
        client,
        email="legacy-grief-state-still-works@example.com",
    )

    journal_response = client.post(
        "/journals",
        json={
            "content": "My parents just died. I feel nothing inside me. I am lost.",
        },
        headers=headers,
    )

    assert journal_response.status_code == 201

    state_response = client.post(
        "/state/calculate",
        headers=headers,
    )

    assert state_response.status_code == 200

    state = state_response.json()

    assert state["stress_level"] is not None
    assert state["emotional_stability"] is not None