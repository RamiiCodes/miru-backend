import pytest

from app.ai.journal_analyzer_factory import get_journal_analyzer
from app.core.config import settings


def test_factory_returns_keyword_analyzer(monkeypatch):
    monkeypatch.setattr(
        settings,
        "journal_analyzer_provider",
        "keyword",
    )

    analyzer = get_journal_analyzer()

    assert analyzer.provider == "keyword"
    assert analyzer.model_name == "keyword_rules_v0_2"
    assert analyzer.prompt_version == "journal_signal_extraction_v0_2"

    result = analyzer.analyze(
        "I can't stop thinking about work. I am not good enough."
    )

    signal_codes = {
        signal.signal_code
        for signal in result.detected_signals
    }

    assert "rumination_tendency" in signal_codes
    assert "self_criticism" in signal_codes
    assert "work_sensitivity" in signal_codes

    assert result.provider == "keyword"
    assert result.model_name == analyzer.model_name
    assert result.prompt_version == analyzer.prompt_version


def test_factory_returns_fake_analyzer(monkeypatch):
    monkeypatch.setattr(
        settings,
        "journal_analyzer_provider",
        "fake",
    )

    analyzer = get_journal_analyzer()

    assert analyzer.provider == "fake"
    assert analyzer.model_name == "fake_journal_analyzer"
    assert analyzer.prompt_version == "journal_signal_extraction_test"

    result = analyzer.analyze("Any content")

    assert len(result.detected_signals) == 1

    detected_signal = result.detected_signals[0]

    assert detected_signal.signal_code == "rumination_tendency"
    assert detected_signal.value == 0.7
    assert detected_signal.confidence == 0.9

    assert result.provider == "fake"


def test_factory_rejects_unsupported_provider(monkeypatch):
    monkeypatch.setattr(
        settings,
        "journal_analyzer_provider",
        "unknown_provider",
    )

    with pytest.raises(ValueError, match="Unsupported journal analyzer provider"):
        get_journal_analyzer()
