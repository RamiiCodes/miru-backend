from app.ai.journal_analyzer import DetectedJournalSignal, JournalAnalysisResult


class FakeJournalAnalyzer:
    provider = "fake"
    model_name = "fake_journal_analyzer"
    prompt_version = "journal_signal_extraction_test"

    def analyze(self, content: str) -> JournalAnalysisResult:
        return JournalAnalysisResult(
            detected_signals=[
                DetectedJournalSignal(
                    signal_code="rumination_tendency",
                    value=0.7,
                    confidence=0.9,
                    evidence="fake evidence",
                    reason="Fake analyzer output for tests.",
                )
            ],
            safety_flags=[],
            language="en",
            provider=self.provider,
            model_name=self.model_name,
            prompt_version=self.prompt_version,
        )