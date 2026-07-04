from typing import Protocol

from pydantic import BaseModel, Field


class DetectedJournalSignal(BaseModel):
    signal_code: str
    value: float = Field(ge=0, le=1)
    confidence: float = Field(ge=0, le=1)
    evidence: str | None = None
    reason: str | None = None


class JournalAnalysisResult(BaseModel):
    detected_signals: list[DetectedJournalSignal]
    safety_flags: list[str] = []
    language: str | None = None

    provider: str
    model_name: str
    prompt_version: str


class JournalAnalyzer(Protocol):
    provider: str
    model_name: str
    prompt_version: str

    def analyze(self, content: str) -> JournalAnalysisResult:
        ...