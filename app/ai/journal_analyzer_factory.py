from app.ai.journal_analyzer import JournalAnalyzer
from app.ai.providers.fake_journal_analyzer import FakeJournalAnalyzer
from app.ai.providers.keyword_journal_analyzer import KeywordJournalAnalyzer
from app.ai.providers.ollama_journal_analyzer import OllamaJournalAnalyzer
from app.core.config import settings


def get_journal_analyzer() -> JournalAnalyzer:
    provider = settings.journal_analyzer_provider.lower().strip()

    if provider == "keyword":
        return KeywordJournalAnalyzer()

    if provider == "fake":
        return FakeJournalAnalyzer()

    if provider == "ollama":
        return OllamaJournalAnalyzer()

    raise ValueError(f"Unsupported journal analyzer provider: {provider}")