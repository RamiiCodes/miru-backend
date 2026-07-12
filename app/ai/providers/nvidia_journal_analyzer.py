import json
import logging
import re
from time import perf_counter
from typing import Any

import httpx
from pydantic import BaseModel, Field, ValidationError, model_validator


from app.ai.journal_analyzer import (
    DetectedJournalSignal,
    JournalAnalysisResult,
    LifeEventCandidate,
)
from app.ai.providers.keyword_journal_analyzer import KeywordJournalAnalyzer
from app.core.config import settings


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
class NvidiaExtractionPayload(BaseModel):
    detected_signals: list[DetectedJournalSignal] = Field(default_factory=list)
    safety_flags: list[str] = Field(default_factory=list)
    themes: list[str] = Field(default_factory=list)
    life_event_candidates: list[LifeEventCandidate] = Field(default_factory=list)
    emotional_tone: str | None = None
    summary: str | None = None
    language: str | None = None

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
            parsed_payload.themes,
            self._themes_from_signals(detected_signals),
            )

            emotional_tone = parsed_payload.emotional_tone

            if emotional_tone is None and themes:
                emotional_tone = ", ".join(themes)

            life_event_candidates = self._filter_life_event_candidates(
                parsed_payload.life_event_candidates
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
                    "safety_flags_after_keyword_merge": safety_flags,
                },
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

    def _build_messages(self, content: str) -> list[dict[str, str]]:
        return [
            {
                "role": "system",
                "content": (
                    "You are Miru's structured journal extraction system.\n"
                    "You extract emotional and cognitive signals from journal text.\n"
                    "You must return structured JSON only.\n"
                    "Do not generate advice.\n"
                    "Do not generate recommendations.\n"
                    "Do not generate therapy-like reflections.\n"
                    "Do not diagnose the user.\n"
                    "Use cautious language.\n"
                    "Only extract what is grounded in the user's text.\n"
                ),
            },
            {
                "role": "user",
                "content": (
                    "Analyze the following journal entry and return JSON matching the schema.\n\n"
                    "Allowed detected signal codes:\n"
                    f"{', '.join(ALLOWED_JOURNAL_SIGNAL_CODES)}\n\n"
                    "Allowed safety flags:\n"
                    f"{', '.join(ALLOWED_SAFETY_FLAGS)}\n\n"
                    "Allowed life event severities:\n"
                    f"{', '.join(ALLOWED_LIFE_EVENT_SEVERITIES)}\n\n"
                    "Rules:\n"
                    "- detected_signals must use only allowed signal_code values.\n"
                    "- value must be between 0 and 1.\n"
                    "- confidence must be between 0 and 1.\n"
                    "- evidence should quote or closely reference the user's wording.\n"
                    "- safety_flags must use only allowed values.\n"
                    "- life_event_candidates should be used only for meaningful life events.\n"
                    "- themes should be short snake_case labels.\n"
                    "- summary must be short and descriptive, not advice.\n"
                    "- If uncertain, lower confidence instead of inventing.\n\n"
                    "life_event_candidates must use this exact object shape:\n"
                    "{\"event_type\": \"bereavement\", \"description\": \"Death of someone close\", \"severity\": \"high\", \"confidence\": 0.8, \"evidence\": \"quoted text\"}\n\n"
                    "Do not use keys like event, type, score, or probability. Use the exact schema keys.\n\n"
                    "Journal entry:\n"
                    f"{content}"
                ),
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
