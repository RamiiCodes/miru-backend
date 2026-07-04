from app.ai.providers.keyword_journal_analyzer import KeywordJournalAnalyzer


def test_keyword_analyzer_detects_matching_signal() -> None:
    analyzer = KeywordJournalAnalyzer()

    result = analyzer.analyze("I can't stop thinking about this work deadline.")

    signal_codes = {
        signal.signal_code
        for signal in result.detected_signals
    }

    assert "rumination_tendency" in signal_codes
    assert "work_sensitivity" in signal_codes


def test_find_matched_keywords_avoids_overlapping_nested_keywords() -> None:
    analyzer = KeywordJournalAnalyzer()

    matched_keywords = analyzer._find_matched_keywords(
        content="I am not good enough.",
        keywords=[
            "not good enough",
            "i am not good enough",
        ],
    )

    assert matched_keywords == ["i am not good enough"]
