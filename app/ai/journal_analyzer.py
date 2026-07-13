from typing import Any, Protocol

from pydantic import BaseModel, Field


class DetectedJournalSignal(BaseModel):
    signal_code: str
    value: float = Field(ge=0, le=1)
    confidence: float = Field(ge=0, le=1)
    evidence: str | None = None
    reason: str | None = None


class LifeEventCandidate(BaseModel):
    event_type: str
    description: str
    severity: str = Field(pattern="^(low|medium|high)$")
    confidence: float = Field(ge=0, le=1)
    evidence: str | None = None

class SemanticDimensionResult(BaseModel):
    value: float = Field(ge=0, le=1)
    confidence: float = Field(ge=0, le=1)
    evidence: str | None = None
    reason: str | None = None


class AdditionalSemanticDimensionResult(SemanticDimensionResult):
    name: str


class SemanticEventCandidateResult(BaseModel):
    category: str | None = None
    event_type: str
    title: str | None = None
    description: str | None = None
    significance: float | None = Field(default=None, ge=0, le=1)
    valence: float | None = Field(default=None, ge=0, le=1)
    confidence: float = Field(ge=0, le=1)
    evidence: str | None = None
    semantic_tags: list[str] = Field(default_factory=list)
    life_domains: list[str] = Field(default_factory=list)


class JournalSemanticFrameResult(BaseModel):
    core_dimensions: dict[str, SemanticDimensionResult] = Field(default_factory=dict)
    emotion_labels: list[str] = Field(default_factory=list)
    semantic_tags: list[str] = Field(default_factory=list)
    life_domains: list[str] = Field(default_factory=list)
    needs: list[str] = Field(default_factory=list)
    additional_dimensions: list[AdditionalSemanticDimensionResult] = Field(
        default_factory=list
    )
    event_candidates: list[SemanticEventCandidateResult] = Field(default_factory=list)
    safety_flags: list[str] = Field(default_factory=list)
    overall_confidence: float | None = Field(default=None, ge=0, le=1)
    raw_output: dict[str, Any] = Field(default_factory=dict)

class JournalAnalysisResult(BaseModel):
    detected_signals: list[DetectedJournalSignal] = []
    safety_flags: list[str] = []

    themes: list[str] = []
    life_event_candidates: list[LifeEventCandidate] = []

    emotional_tone: str | None = None
    summary: str | None = None
    language: str | None = None

    provider: str
    model_name: str
    prompt_version: str

    raw_output: dict | None = None
    semantic_frame: JournalSemanticFrameResult | None = None


class JournalAnalyzer(Protocol):
    provider: str
    model_name: str
    prompt_version: str

    def analyze(self, content: str) -> JournalAnalysisResult:
        ...