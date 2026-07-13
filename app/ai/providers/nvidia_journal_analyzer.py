import json
import logging
import re
from time import perf_counter
from typing import Any

import httpx
from pydantic import BaseModel, Field, ValidationError, model_validator


from app.ai.providers.keyword_journal_analyzer import KeywordJournalAnalyzer
from app.core.config import settings

from app.ai.journal_analyzer import (
    AdditionalSemanticDimensionResult,
    DetectedJournalSignal,
    JournalAnalysisResult,
    JournalSemanticFrameResult,
    LifeEventCandidate,
    SemanticDimensionResult,
    SemanticEventCandidateResult,
)

logger = logging.getLogger(__name__)


_USE_SETTINGS = object()


ALLOWED_JOURNAL_SIGNAL_CODES = [
    "rumination_tendency",
    "self_criticism",
    "fear_of_failure",
    "work_sensitivity",
    "grief_loss",
    "emotional_numbness",
    "disorientation",
    "loneliness",
    "overwhelm",
]

ALLOWED_SAFETY_FLAGS = [
    "self_harm_risk",
    "harm_to_others_risk",
    "abuse_or_coercion_context",
    "severe_distress",
]

ALLOWED_LIFE_EVENT_SEVERITIES = [
    "low",
    "medium",
    "high",
]

def _normalize_float(
    value,
    default: float,
) -> float:
    try:
        parsed_value = float(value)
    except (TypeError, ValueError):
        return default

    return max(0.0, min(1.0, parsed_value))


def _normalize_string_list(value) -> list[str]:
    if value is None:
        return []

    if isinstance(value, str):
        return [value]

    if not isinstance(value, list):
        return []

    normalized_values: list[str] = []

    for item in value:
        if isinstance(item, str):
            normalized_values.append(item)
        elif isinstance(item, dict):
            possible_value = (
                item.get("flag")
                or item.get("flag_type")
                or item.get("theme")
                or item.get("name")
                or item.get("value")
            )

            if isinstance(possible_value, str):
                normalized_values.append(possible_value)

    return normalized_values


def _normalize_detected_signal(signal: dict) -> dict:
    signal_code = (
        signal.get("signal_code")
        or signal.get("signal")
        or signal.get("code")
        or signal.get("type")
    )

    return {
        "signal_code": signal_code,
        "value": _normalize_float(
            signal.get("value")
            or signal.get("score")
            or signal.get("intensity")
            or signal.get("severity_score"),
            default=0.6,
        ),
        "confidence": _normalize_float(
            signal.get("confidence")
            or signal.get("certainty")
            or signal.get("probability"),
            default=0.6,
        ),
        "evidence": signal.get("evidence") or signal.get("quote"),
        "reason": signal.get("reason") or signal.get("explanation"),
    }


def _normalize_life_event_type(raw_event_type: str | None) -> str:
    if not raw_event_type:
        return "unknown_life_event"

    normalized = raw_event_type.lower().strip()

    bereavement_terms = [
        "bereavement",
        "death",
        "loss",
        "lost",
        "dead",
        "died",
        "funeral",
        "loss of dead",
        "loss of parent",
        "loss of parents",
    ]

    if any(term in normalized for term in bereavement_terms):
        return "bereavement"

    return normalized.replace(" ", "_")


def _normalize_life_event_candidate(candidate: dict) -> dict:
    raw_event_type = (
        candidate.get("event_type")
        or candidate.get("event")
        or candidate.get("type")
        or candidate.get("life_event_type")
        or candidate.get("name")
    )

    event_type = _normalize_life_event_type(raw_event_type)

    description = (
        candidate.get("description")
        or candidate.get("summary")
        or candidate.get("event")
        or raw_event_type
        or "Possible life event detected."
    )

    severity = candidate.get("severity") or "medium"

    if severity not in ALLOWED_LIFE_EVENT_SEVERITIES:
        severity = "medium"

    return {
        "event_type": event_type,
        "description": description,
        "severity": severity,
        "confidence": _normalize_float(
            candidate.get("confidence")
            or candidate.get("score")
            or candidate.get("probability"),
            default=0.6,
        ),
        "evidence": candidate.get("evidence") or candidate.get("quote"),
    }
class NvidiaSemanticDimension(BaseModel):
    value: float = Field(ge=0, le=1)
    confidence: float = Field(ge=0, le=1)
    evidence: str | None = None
    reason: str | None = None


class NvidiaCoreDimensions(BaseModel):
    valence: NvidiaSemanticDimension | None = None
    arousal: NvidiaSemanticDimension | None = None
    threat: NvidiaSemanticDimension | None = None
    control: NvidiaSemanticDimension | None = None
    social_connection: NvidiaSemanticDimension | None = None
    uncertainty: NvidiaSemanticDimension | None = None
    self_evaluation: NvidiaSemanticDimension | None = None
    energy: NvidiaSemanticDimension | None = None


class NvidiaAdditionalSemanticDimension(NvidiaSemanticDimension):
    name: str


class NvidiaSemanticEventCandidate(BaseModel):
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
class NvidiaExtractionPayload(BaseModel):
    # Legacy compatibility fields.
    detected_signals: list[DetectedJournalSignal] = Field(default_factory=list)
    safety_flags: list[str] = Field(default_factory=list)
    themes: list[str] = Field(default_factory=list)
    life_event_candidates: list[LifeEventCandidate] = Field(default_factory=list)
    emotional_tone: str | None = None
    summary: str | None = None
    language: str | None = None

    # New generic semantic frame fields.
    core_dimensions: NvidiaCoreDimensions = Field(default_factory=NvidiaCoreDimensions)
    emotion_labels: list[str] = Field(default_factory=list)
    semantic_tags: list[str] = Field(default_factory=list)
    life_domains: list[str] = Field(default_factory=list)
    needs: list[str] = Field(default_factory=list)
    additional_dimensions: list[NvidiaAdditionalSemanticDimension] = Field(
        default_factory=list
    )
    event_candidates: list[NvidiaSemanticEventCandidate] = Field(default_factory=list)
    overall_confidence: float | None = Field(default=None, ge=0, le=1)

    @model_validator(mode="before")
    @classmethod
    def normalize_llm_payload(cls, data):
        if not isinstance(data, dict):
            return data

        normalized_data = dict(data)

        normalized_data["detected_signals"] = [
            _normalize_detected_signal(signal)
            for signal in normalized_data.get("detected_signals", [])
            if isinstance(signal, dict)
        ]

        normalized_data["life_event_candidates"] = [
            _normalize_life_event_candidate(candidate)
            for candidate in normalized_data.get("life_event_candidates", [])
            if isinstance(candidate, dict)
        ]

        normalized_data["safety_flags"] = _normalize_string_list(
            normalized_data.get("safety_flags", [])
        )

        normalized_data["themes"] = _normalize_string_list(
            normalized_data.get("themes", [])
        )

        return normalized_data


class NvidiaJournalAnalyzer:
    provider = "nvidia"
    prompt_version = "journal_signal_extraction_nvidia_v0_1"

    def _build_semantic_frame_from_payload(
        self,
        parsed_payload: NvidiaExtractionPayload,
        safety_flags: list[str],
    ) -> JournalSemanticFrameResult:
        core_dimensions: dict[str, SemanticDimensionResult] = {}

        for dimension_name in [
            "valence",
            "arousal",
            "threat",
            "control",
            "social_connection",
            "uncertainty",
            "self_evaluation",
            "energy",
        ]:
            dimension = getattr(
                parsed_payload.core_dimensions,
                dimension_name,
            )

            if dimension is None:
                continue

            core_dimensions[dimension_name] = SemanticDimensionResult(
                value=dimension.value,
                confidence=dimension.confidence,
                evidence=dimension.evidence,
                reason=dimension.reason,
            )

        additional_dimensions = [
            AdditionalSemanticDimensionResult(
                name=dimension.name,
                value=dimension.value,
                confidence=dimension.confidence,
                evidence=dimension.evidence,
                reason=dimension.reason,
            )
            for dimension in parsed_payload.additional_dimensions
        ]

        event_candidates = [
            SemanticEventCandidateResult(
                category=candidate.category,
                event_type=candidate.event_type,
                title=candidate.title,
                description=candidate.description,
                significance=candidate.significance,
                valence=candidate.valence,
                confidence=candidate.confidence,
                evidence=candidate.evidence,
                semantic_tags=self._normalize_string_list(candidate.semantic_tags),
                life_domains=self._normalize_string_list(candidate.life_domains),
            )
            for candidate in parsed_payload.event_candidates
        ]

        return JournalSemanticFrameResult(
            core_dimensions=core_dimensions,
            emotion_labels=self._normalize_string_list(parsed_payload.emotion_labels),
            semantic_tags=self._normalize_string_list(parsed_payload.semantic_tags),
            life_domains=self._normalize_string_list(parsed_payload.life_domains),
            needs=self._normalize_string_list(parsed_payload.needs),
            additional_dimensions=additional_dimensions,
            event_candidates=event_candidates,
            safety_flags=safety_flags,
            overall_confidence=parsed_payload.overall_confidence,
            raw_output={
                "source": "nvidia_direct_semantic_extraction",
                "provider": self.provider,
                "model_name": self.model_name,
                "prompt_version": self.prompt_version,
            },
        )

    def _normalize_string_list(
        self,
        values: list[str],
    ) -> list[str]:
        normalized_values: list[str] = []
        seen_values: set[str] = set()

        for value in values:
            normalized_value = value.strip().lower().replace(" ", "_")

            if not normalized_value:
                continue

            if normalized_value in seen_values:
                continue

            seen_values.add(normalized_value)
            normalized_values.append(normalized_value)

        return normalized_values

    def _legacy_life_event_candidates_from_semantic_events(
        self,
        event_candidates: list[NvidiaSemanticEventCandidate],
    ) -> list[LifeEventCandidate]:
        legacy_candidates: list[LifeEventCandidate] = []

        for candidate in event_candidates:
            legacy_candidates.append(
                LifeEventCandidate(
                    event_type=candidate.event_type,
                    description=(
                        candidate.description
                        or candidate.title
                        or candidate.event_type.replace("_", " ").title()
                    ),
                    severity=self._severity_from_significance(candidate.significance),
                    confidence=candidate.confidence,
                    evidence=candidate.evidence,
                )
            )

        return legacy_candidates

    def _severity_from_significance(
        self,
        significance: float | None,
    ) -> str:
        if significance is None:
            return "medium"

        if significance >= 0.75:
            return "high"

        if significance >= 0.4:
            return "medium"

        return "low"

    def __init__(
        self,
        model_name: str | None = None,
        api_key: str | None | object = _USE_SETTINGS,
        base_url: str | None = None,
        timeout_seconds: int | None = None,
        max_tokens: int | None = None,
        fallback_analyzer: KeywordJournalAnalyzer | None = None,
    ) -> None:
        self.model_name = model_name or settings.nvidia_nim_model
        self.api_key = (
            settings.nvidia_api_key
            if api_key is _USE_SETTINGS
            else api_key
        )
        self.base_url = (base_url or settings.nvidia_nim_base_url).rstrip("/")
        self.timeout_seconds = timeout_seconds or settings.nvidia_nim_timeout_seconds
        self.max_tokens = max_tokens or settings.nvidia_nim_max_tokens
        self.fallback_analyzer = fallback_analyzer or KeywordJournalAnalyzer()

    def analyze(self, content: str) -> JournalAnalysisResult:
        self._debug_log(
            "NVIDIA analyzer selected",
            extra={
                "provider": self.provider,
                "model": self.model_name,
                "base_url": self.base_url,
                "api_key_configured": bool(self.api_key),
            },
        )

        if not self.api_key:
            return self._fallback(
                content=content,
                error_message="NVIDIA_API_KEY is not configured.",
            )

        try:
            raw_content = self._call_nvidia(content=content)
            parsed_payload = self._parse_llm_response(raw_content=raw_content)

            keyword_result = self.fallback_analyzer.analyze(content)

            safety_flags = self._merge_unique(
                parsed_payload.safety_flags,
                keyword_result.safety_flags,
            )

            detected_signals = self._filter_detected_signals(
                parsed_payload.detected_signals
            )

            themes = self._merge_unique(
                parsed_payload.semantic_tags,
                self._merge_unique(
                    parsed_payload.themes,
                    self._themes_from_signals(detected_signals),
                ),
            )

            emotional_tone = parsed_payload.emotional_tone

            if emotional_tone is None and parsed_payload.emotion_labels:
                emotional_tone = ", ".join(parsed_payload.emotion_labels)

            if emotional_tone is None and themes:
                emotional_tone = ", ".join(themes)

            legacy_life_event_candidates = list(parsed_payload.life_event_candidates)

            if not legacy_life_event_candidates and parsed_payload.event_candidates:
                legacy_life_event_candidates = (
                    self._legacy_life_event_candidates_from_semantic_events(
                        parsed_payload.event_candidates
                    )
                )

            life_event_candidates = self._filter_life_event_candidates(
                legacy_life_event_candidates
            )
            semantic_frame = self._build_semantic_frame_from_payload(
                parsed_payload=parsed_payload,
                safety_flags=safety_flags,
            )

            self._debug_log(
                "NVIDIA extraction succeeded",
                extra={
                    "provider": self.provider,
                    "model": self.model_name,
                    "signals_count": len(detected_signals),
                    "themes_count": len(themes),
                    "life_event_candidates_count": len(life_event_candidates),
                    "safety_flags_count": len(safety_flags),
                },
            )

            return JournalAnalysisResult(
                detected_signals=detected_signals,
                safety_flags=safety_flags,
                themes=themes,
                life_event_candidates=life_event_candidates,
                emotional_tone=emotional_tone,
                summary=parsed_payload.summary,
                language=parsed_payload.language,
                provider=self.provider,
                model_name=self.model_name,
                prompt_version=self.prompt_version,
                raw_output={
                    "provider": self.provider,
                    "model_name": self.model_name,
                    "prompt_version": self.prompt_version,
                    "llm_payload": parsed_payload.model_dump(mode="json"),
                    "semantic_frame": semantic_frame.model_dump(mode="json"),
                    "safety_flags_after_keyword_merge": safety_flags,
                },
                semantic_frame=semantic_frame,
            )

        except Exception as exc:
            return self._fallback(
                content=content,
                error_message=str(exc),
            )

    def _call_nvidia(self, content: str) -> str:
        url = f"{self.base_url}/chat/completions"

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": self.model_name,
            "messages": self._build_messages(content=content),
            "temperature": 0,
            "max_tokens": self.max_tokens,
            "stream": False,
           "nvext": {
            "guided_json": NvidiaExtractionPayload.model_json_schema()
                
            },
        }

        self._debug_log(
            "Calling NVIDIA NIM endpoint",
            extra={
                "url": url,
                "model": self.model_name,
                "timeout_seconds": self.timeout_seconds,
                "max_tokens": self.max_tokens,
                "journal_character_count": len(content),
                "guided_json_enabled": True,

            },
        )

        start_time = perf_counter()
        timeout = httpx.Timeout(
        connect=10.0,
        read=float(self.timeout_seconds),
        write=10.0,
        pool=10.0,
    )

        with httpx.Client(timeout=timeout) as client:
            response = client.post(
                url,
                headers=headers,
                json=payload,
            )

        latency_ms = int((perf_counter() - start_time) * 1000)

        self._debug_log(
            "NVIDIA NIM response received",
            extra={
                "status_code": response.status_code,
                "latency_ms": latency_ms,
                "model": self.model_name,
            },
        )

        response.raise_for_status()

        response_json = response.json()

        try:
            return response_json["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise ValueError(
                "Unexpected NVIDIA response format."
            ) from exc

    def _build_messages(
        self,
        content: str,
    ) -> list[dict[str, str]]:
        system_message = (
            "You are Miru's semantic journal extraction component. "
            "Your task is to extract structured meaning from a user's journal entry. "
            "You are not a therapist. Do not diagnose. Do not recommend actions. "
            "Do not give advice. Return JSON only."
        )

        user_message = (
            "Extract both legacy compatibility fields and a generic semantic frame.\n\n"
            "Important architecture rule:\n"
            "- The LLM is a flexible semantic interpreter.\n"
            "- The backend is responsible for validation, scoring, safety, memory, and personalization.\n"
            "- Do not decide final recommendations.\n\n"
            "Do not force the user's experience into predefined emotion labels. "
            "Use open-ended emotion_labels, semantic_tags, life_domains, and needs when needed.\n\n"
            "Always provide core_dimensions when there is enough evidence. "
            "If there is not enough evidence for a dimension, leave that dimension null.\n\n"
            "Core dimensions use values from 0 to 1:\n"
            "- valence: negative to positive emotional tone\n"
            "- arousal: calm/deactivated to activated/intense\n"
            "- threat: felt danger, pressure, alarm, or risk\n"
            "- control: sense of agency and ability to act\n"
            "- social_connection: isolation/rejection to connection/support\n"
            "- uncertainty: clarity/certainty to uncertainty/confusion\n"
            "- self_evaluation: self-criticism/shame to self-acceptance/pride\n"
            "- energy: depleted to energized\n\n"
            "For every provided core dimension, include:\n"
            '{ "value": number, "confidence": number, "evidence": string|null, "reason": string|null }\n\n'
            "Open-ended fields:\n"
            "- emotion_labels: natural labels such as happy, anxious, numb, conflicted, relieved\n"
            "- semantic_tags: snake_case tags such as mixed_emotion, major_transition, low_clarity\n"
            "- life_domains: domains such as relationship, career, family, health, identity, future_planning\n"
            "- needs: inferred needs such as grounding, connection, celebration, clarity, rest, support\n"
            "- additional_dimensions: extra dimensions only when the core dimensions do not capture something important\n\n"
            "Event candidates:\n"
            "- Use event_candidates for meaningful factual life events only.\n"
            "- event_type is open-ended. Do not restrict it to a predefined list.\n"
            "- category should be broad, for example: family, relationship, career, education, health, financial, relocation, legal, trauma, achievement, personal_growth, other.\n"
            "- Do not create an event candidate for a passing emotion like 'I felt anxious today'.\n\n"
            "Legacy compatibility fields:\n"
            "- detected_signals may use existing known signal codes if clearly applicable.\n"
            "- themes may summarize important recurring themes.\n"
            "- life_event_candidates may be filled for backward compatibility, but event_candidates is the preferred new field.\n\n"
            "Allowed legacy detected signal codes:\n"
            "- rumination_tendency\n"
            "- self_criticism\n"
            "- fear_of_failure\n"
            "- work_sensitivity\n"
            "- grief_loss\n"
            "- emotional_numbness\n"
            "- disorientation\n"
            "- loneliness\n"
            "- overwhelm\n\n"
            "Allowed safety flags:\n"
            "- self_harm_risk\n"
            "- harm_to_others_risk\n"
            "- abuse_or_coercion_context\n"
            "- severe_distress\n\n"
            "Journal entry:\n"
            f"{content}"
        )

        return [
            {
                "role": "system",
                "content": system_message,
            },
            {
                "role": "user",
                "content": user_message,
            },
        ]

    def _parse_llm_response(
        self,
        raw_content: str,
    ) -> NvidiaExtractionPayload:
        parsed_json = self._load_json(raw_content=raw_content)

        try:
            parsed_payload = NvidiaExtractionPayload.model_validate(parsed_json)
        except ValidationError as exc:
            raise ValueError(
                f"NVIDIA extraction JSON failed validation: {exc}"
            ) from exc

        self._debug_log(
            "NVIDIA JSON parsed and validated",
            extra={
                "signals_count": len(parsed_payload.detected_signals),
                "themes_count": len(parsed_payload.themes),
                "life_event_candidates_count": len(parsed_payload.life_event_candidates),
                "safety_flags_count": len(parsed_payload.safety_flags),
            },
        )

        return parsed_payload

    def _load_json(self, raw_content: str) -> dict[str, Any]:
        try:
            return json.loads(raw_content)
        except json.JSONDecodeError:
            pass

        json_match = re.search(
            r"\{.*\}",
            raw_content,
            flags=re.DOTALL,
        )

        if not json_match:
            raise ValueError("NVIDIA response did not contain valid JSON.")

        try:
            return json.loads(json_match.group(0))
        except json.JSONDecodeError as exc:
            raise ValueError(
                "NVIDIA response contained invalid JSON."
            ) from exc

    def _filter_detected_signals(
        self,
        detected_signals: list[DetectedJournalSignal],
    ) -> list[DetectedJournalSignal]:
        filtered_signals: list[DetectedJournalSignal] = []
        seen_signal_codes: set[str] = set()

        for signal in detected_signals:
            if signal.signal_code not in ALLOWED_JOURNAL_SIGNAL_CODES:
                continue

            if signal.signal_code in seen_signal_codes:
                continue

            seen_signal_codes.add(signal.signal_code)
            if signal.reason is None:
                signal = signal.model_copy(
                update={
                    "reason": (
                    f"NVIDIA extracted {signal.signal_code} from the journal evidence."
                                )
        }
    )
            filtered_signals.append(signal)

        return filtered_signals

    def _filter_life_event_candidates(
        self,
        candidates: list[LifeEventCandidate],
    ) -> list[LifeEventCandidate]:
        filtered_candidates: list[LifeEventCandidate] = []

        for candidate in candidates:
            if candidate.severity not in ALLOWED_LIFE_EVENT_SEVERITIES:
                continue

            filtered_candidates.append(candidate)

        return filtered_candidates

    def _themes_from_signals(
        self,
        detected_signals: list[DetectedJournalSignal],
    ) -> list[str]:
        signal_theme_map = {
            "rumination_tendency": "rumination",
            "self_criticism": "self_criticism",
            "fear_of_failure": "fear_of_failure",
            "work_sensitivity": "work_stress",
            "grief_loss": "grief",
            "emotional_numbness": "emotional_numbness",
            "disorientation": "disorientation",
            "loneliness": "loneliness",
            "overwhelm": "overwhelm",
        }
        

        return [
            signal_theme_map[signal.signal_code]
            for signal in detected_signals
            if signal.signal_code in signal_theme_map
        ]

    def _merge_unique(
        self,
        first_values: list[str],
        second_values: list[str],
    ) -> list[str]:
        merged_values: list[str] = []

        for value in first_values + second_values:
            if value not in merged_values:
                merged_values.append(value)

        return merged_values

    def _fallback(
        self,
        content: str,
        error_message: str,
    ) -> JournalAnalysisResult:
        self._debug_log(
            "NVIDIA analyzer fallback used",
            extra={
                "attempted_provider": self.provider,
                "attempted_model": self.model_name,
                "error": error_message,
            },
        )

        fallback_result = self.fallback_analyzer.analyze(content)

        raw_output = fallback_result.raw_output or {}

        fallback_result.raw_output = {
            **raw_output,
            "nvidia_fallback_used": True,
            "nvidia_error": error_message,
            "attempted_provider": self.provider,
            "attempted_model_name": self.model_name,
            "attempted_prompt_version": self.prompt_version,
        }

        return fallback_result

    def _debug_log(
        self,
        message: str,
        extra: dict[str, Any] | None = None,
    ) -> None:
        if not getattr(settings, "journal_analyzer_debug", False):
            return

        safe_extra = extra or {}

        logger.warning(
            "[Miru JournalAnalyzer Debug] %s | %s",
            message,
            safe_extra,
        )
