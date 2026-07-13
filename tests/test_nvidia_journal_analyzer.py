from app.ai.providers.nvidia_journal_analyzer import NvidiaJournalAnalyzer


def test_nvidia_journal_analyzer_parses_structured_json(monkeypatch):
    analyzer = NvidiaJournalAnalyzer(
        api_key="fake-key",
        model_name="mistralai/mistral-medium-3.5-128b",
    )

    def fake_call_nvidia(content: str) -> str:
        return """
        {
          "detected_signals": [
            {
              "signal_code": "grief_loss",
              "value": 0.95,
              "confidence": 0.9,
              "evidence": "My parents just died",
              "reason": "The user describes the death of parents."
            },
            {
              "signal_code": "emotional_numbness",
              "value": 0.9,
              "confidence": 0.85,
              "evidence": "I feel nothing inside me",
              "reason": "The user describes emotional numbness."
            },
            {
              "signal_code": "disorientation",
              "value": 0.75,
              "confidence": 0.8,
              "evidence": "I am lost",
              "reason": "The user describes feeling lost."
            }
          ],
          "safety_flags": [],
          "themes": ["grief", "emotional_numbness", "disorientation"],
          "life_event_candidates": [
            {
              "event_type": "bereavement",
              "description": "Death of parents",
              "severity": "high",
              "confidence": 0.9,
              "evidence": "My parents just died"
            }
          ],
          "emotional_tone": "numb, lost, grieving",
          "summary": "The user describes a major bereavement with emotional numbness.",
          "language": "en"
        }
        """

    monkeypatch.setattr(
        analyzer,
        "_call_nvidia",
        fake_call_nvidia,
    )

    result = analyzer.analyze(
        "My parents just died. I feel nothing inside me. I am lost."
    )

    assert result.provider == "nvidia"
    assert result.model_name == "mistralai/mistral-medium-3.5-128b"
    assert result.prompt_version == "journal_signal_extraction_nvidia_v0_1"

    signal_codes = {
        signal.signal_code
        for signal in result.detected_signals
    }

    assert "grief_loss" in signal_codes
    assert "emotional_numbness" in signal_codes
    assert "disorientation" in signal_codes

    assert "grief" in result.themes
    assert "emotional_numbness" in result.themes
    assert "disorientation" in result.themes

    assert result.life_event_candidates
    assert result.life_event_candidates[0].event_type == "bereavement"
    assert result.life_event_candidates[0].severity == "high"


def test_nvidia_journal_analyzer_filters_unknown_signal_codes(monkeypatch):
    analyzer = NvidiaJournalAnalyzer(
        api_key="fake-key",
        model_name="mistralai/mistral-medium-3.5-128b",
    )

    def fake_call_nvidia(content: str) -> str:
        return """
        {
          "detected_signals": [
            {
              "signal_code": "unknown_signal",
              "value": 0.9,
              "confidence": 0.9,
              "evidence": "some text",
              "reason": "Invalid code."
            },
            {
              "signal_code": "loneliness",
              "value": 0.8,
              "confidence": 0.85,
              "evidence": "I feel alone",
              "reason": "The user describes loneliness."
            }
          ],
          "safety_flags": [],
          "themes": ["loneliness"],
          "life_event_candidates": [],
          "emotional_tone": "lonely",
          "summary": "The user describes loneliness.",
          "language": "en"
        }
        """

    monkeypatch.setattr(
        analyzer,
        "_call_nvidia",
        fake_call_nvidia,
    )

    result = analyzer.analyze("I feel alone.")

    signal_codes = {
        signal.signal_code
        for signal in result.detected_signals
    }

    assert "unknown_signal" not in signal_codes
    assert "loneliness" in signal_codes


def test_nvidia_journal_analyzer_falls_back_to_keyword_when_api_key_missing():
    analyzer = NvidiaJournalAnalyzer(
        api_key=None,
        model_name="mistralai/mistral-medium-3.5-128b",
    )

    result = analyzer.analyze(
        "I can't stop thinking about work. I am not good enough."
    )

    assert result.provider == "keyword"
    assert result.raw_output is not None
    assert result.raw_output["nvidia_fallback_used"] is True
    assert result.raw_output["attempted_provider"] == "nvidia"

    signal_codes = {
        signal.signal_code
        for signal in result.detected_signals
    }

    assert "rumination_tendency" in signal_codes
    assert "self_criticism" in signal_codes
    assert "work_sensitivity" in signal_codes


def test_nvidia_journal_analyzer_falls_back_to_keyword_when_json_invalid(monkeypatch):
    analyzer = NvidiaJournalAnalyzer(
        api_key="fake-key",
        model_name="mistralai/mistral-medium-3.5-128b",
    )

    def fake_call_nvidia(content: str) -> str:
        return "this is not json"

    monkeypatch.setattr(
        analyzer,
        "_call_nvidia",
        fake_call_nvidia,
    )

    result = analyzer.analyze(
        "I can't stop thinking about work. I am not good enough."
    )

    assert result.provider == "keyword"
    assert result.raw_output is not None
    assert result.raw_output["nvidia_fallback_used"] is True

    signal_codes = {
        signal.signal_code
        for signal in result.detected_signals
    }

    assert "rumination_tendency" in signal_codes
    assert "self_criticism" in signal_codes


def test_nvidia_journal_analyzer_merges_keyword_safety_flags(monkeypatch):
    analyzer = NvidiaJournalAnalyzer(
        api_key="fake-key",
        model_name="mistralai/mistral-medium-3.5-128b",
    )

    def fake_call_nvidia(content: str) -> str:
        return """
        {
          "detected_signals": [
            {
              "signal_code": "overwhelm",
              "value": 0.8,
              "confidence": 0.8,
              "evidence": "cannot cope",
              "reason": "The user describes overwhelm."
            }
          ],
          "safety_flags": [],
          "themes": ["overwhelm"],
          "life_event_candidates": [],
          "emotional_tone": "overwhelmed",
          "summary": "The user describes severe overwhelm.",
          "language": "en"
        }
        """

    monkeypatch.setattr(
        analyzer,
        "_call_nvidia",
        fake_call_nvidia,
    )

    result = analyzer.analyze(
        "I am in severe distress and I cannot cope tonight."
    )

    assert result.provider == "nvidia"
    assert "severe_distress" in result.safety_flags

def test_nvidia_journal_analyzer_normalizes_imperfect_life_event_json(monkeypatch):
    analyzer = NvidiaJournalAnalyzer(
        api_key="fake-key",
        model_name="nvidia/nemotron-3-nano-30b-a3b",
    )

    def fake_call_nvidia(content: str) -> str:
        return """
        {
          "detected_signals": [
            {
              "signal_code": "grief_loss",
              "value": 0.9,
              "confidence": 0.8,
              "evidence": "parents just died",
              "reason": "The user describes a major loss."
            }
          ],
          "safety_flags": [],
          "themes": ["grief"],
          "life_event_candidates": [
            {
              "event": "loss of dead",
              "severity": "high"
            }
          ],
          "emotional_tone": "grieving",
          "summary": "The user describes a major loss.",
          "language": "en"
        }
        """

    monkeypatch.setattr(
        analyzer,
        "_call_nvidia",
        fake_call_nvidia,
    )

    result = analyzer.analyze(
        "My parents just died. I feel nothing inside me. I am lost."
    )

    assert result.provider == "nvidia"

    assert result.life_event_candidates
    assert result.life_event_candidates[0].event_type == "bereavement"
    assert result.life_event_candidates[0].description == "loss of dead"
    assert result.life_event_candidates[0].severity == "high"
    assert result.life_event_candidates[0].confidence == 0.6


def test_nvidia_journal_analyzer_returns_direct_semantic_frame(monkeypatch):
    analyzer = NvidiaJournalAnalyzer(
        api_key="fake-key",
        model_name="mistralai/mistral-medium-3.5-128b",
    )

    def fake_call_nvidia(content: str) -> str:
        return """
        {
          "detected_signals": [],
          "safety_flags": [],
          "themes": [],
          "life_event_candidates": [],
          "emotional_tone": "happy, excited",
          "summary": "The user describes feeling happy after getting engaged.",
          "language": "en",
          "core_dimensions": {
            "valence": {
              "value": 0.95,
              "confidence": 0.95,
              "evidence": "I am so happy",
              "reason": "The user directly says they are very happy."
            },
            "arousal": {
              "value": 0.75,
              "confidence": 0.8,
              "evidence": "so happy",
              "reason": "The wording suggests activated positive emotion."
            },
            "social_connection": {
              "value": 0.95,
              "confidence": 0.9,
              "evidence": "I got engaged today",
              "reason": "Engagement is a relationship milestone."
            },
            "threat": {
              "value": 0.05,
              "confidence": 0.7,
              "evidence": null,
              "reason": "No threat or danger is expressed."
            }
          },
          "emotion_labels": ["happy", "excited"],
          "semantic_tags": [
            "positive_life_event",
            "relationship_milestone",
            "major_transition"
          ],
          "life_domains": ["relationship", "future_planning"],
          "needs": ["celebration", "connection", "emotional_integration"],
          "additional_dimensions": [
            {
              "name": "anticipation",
              "value": 0.8,
              "confidence": 0.75,
              "evidence": "got engaged today",
              "reason": "Engagement points toward future planning."
            }
          ],
          "event_candidates": [
            {
              "category": "relationship",
              "event_type": "engagement",
              "title": "Got engaged",
              "description": "The user got engaged today.",
              "significance": 0.9,
              "valence": 0.95,
              "confidence": 0.95,
              "evidence": "I got engaged today",
              "semantic_tags": [
                "relationship_milestone",
                "major_transition"
              ],
              "life_domains": [
                "relationship",
                "future_planning"
              ]
            }
          ],
          "overall_confidence": 0.9
        }
        """

    monkeypatch.setattr(
        analyzer,
        "_call_nvidia",
        fake_call_nvidia,
    )

    result = analyzer.analyze(
        "I am so happy, I got engaged today."
    )

    assert result.provider == "nvidia"
    assert result.semantic_frame is not None

    semantic_frame = result.semantic_frame

    assert semantic_frame.core_dimensions["valence"].value == 0.95
    assert semantic_frame.core_dimensions["social_connection"].value == 0.95

    assert "happy" in semantic_frame.emotion_labels
    assert "relationship_milestone" in semantic_frame.semantic_tags
    assert "relationship" in semantic_frame.life_domains
    assert "celebration" in semantic_frame.needs

    assert semantic_frame.additional_dimensions
    assert semantic_frame.additional_dimensions[0].name == "anticipation"

    assert semantic_frame.event_candidates
    assert semantic_frame.event_candidates[0].event_type == "engagement"
    assert semantic_frame.event_candidates[0].category == "relationship"
    assert semantic_frame.event_candidates[0].significance == 0.9

    assert result.life_event_candidates
    assert result.life_event_candidates[0].event_type == "engagement"
    assert result.life_event_candidates[0].severity == "high"

    assert result.raw_output["semantic_frame"]["raw_output"]["source"] == (
        "nvidia_direct_semantic_extraction"
    )
