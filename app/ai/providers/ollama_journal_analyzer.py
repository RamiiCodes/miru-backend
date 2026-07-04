import json
from signal import signal

import httpx
from pydantic import ValidationError

from app.ai.journal_analyzer import JournalAnalysisResult
from app.core.config import settings


ALLOWED_SIGNAL_CODES = [
    "rumination_tendency",
    "self_criticism",
    "fear_of_failure",
    "work_sensitivity",
]

ALLOWED_SAFETY_FLAGS = [
    "self_harm_risk",
    "harm_to_others_risk",
    "abuse_or_coercion_context",
    "severe_distress",
]

JOURNAL_SIGNAL_EXTRACTION_SCHEMA = {
    "type": "object",
    "properties": {
        "detected_signals": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "signal_code": {
                        "type": "string",
                        "enum": ALLOWED_SIGNAL_CODES,
                    },
                    "value": {
                        "type": "number",
                        "minimum": 0,
                        "maximum": 1,
                    },
                    "confidence": {
                        "type": "number",
                        "minimum": 0,
                        "maximum": 1,
                    },
                    "evidence": {
                        "type": ["string", "null"],
                    },
                    "reason": {
                        "type": ["string", "null"],
                    },
                },
                "required": [
                    "signal_code",
                    "value",
                    "confidence",
                    "evidence",
                    "reason",
                ],
                "additionalProperties": False,
            },
        },
        "safety_flags": {
            "type": "array",
            "items": {
                "type": "string",
                "enum": ALLOWED_SAFETY_FLAGS,
    },
},
        "language": {
            "type": ["string", "null"],
        },
    },
    "required": [
        "detected_signals",
        "safety_flags",
        "language",
    ],
    "additionalProperties": False,
}


SYSTEM_PROMPT = """
You are Miru's journal signal extraction engine.

Your task is to extract structured emotional and cognitive signals from a user's journal entry.

You must follow these rules:
- Return only valid JSON matching the provided schema.
- Do not diagnose the user.
- Do not mention medical conditions.
- Do not give advice.
- Do not invent signal codes.
- Only use allowed signal codes.
- Use evidence as a short quote or phrase from the journal.
- Use confidence conservatively.

Allowed signal codes:
- rumination_tendency: repetitive, looping, intrusive, or stuck thoughts
- self_criticism: harsh self-judgment, shame, self-blame, feeling not good enough
- fear_of_failure: fear of failing, perceived failure, avoidance due to possible failure
- work_sensitivity: work, manager, colleague, project, deadline, workplace conflict, pressure

Safety flag rules:
- Use safety_flags only for explicit serious risk signals.
- Do not use severity words such as "low", "medium", or "high" as safety flags.
- Do not use signal codes as safety flags.
- If there is no clear serious risk, return an empty list: [].

Evidence rules:
- Evidence must be an exact short quote from the journal entry.
- Do not paraphrase evidence.
- If no exact quote supports the signal, set evidence to null.

Confidence rules:
- Do not use confidence 1.0.
- Use confidence above 0.8 only when the signal is very explicit.

Value scale:
- 0.1 to 0.3 = weak signal
- 0.4 to 0.6 = moderate signal
- 0.7 to 1.0 = strong signal

Confidence scale:
- 0.1 to 0.4 = uncertain
- 0.5 to 0.7 = reasonable
- 0.8 to 1.0 = strong evidence
""".strip()


class OllamaJournalAnalyzer:
    provider = "ollama"
    prompt_version = "journal_signal_extraction_v0_1"

    def __init__(self) -> None:
        self.base_url = settings.ollama_base_url.rstrip("/")
        self.model_name = settings.ollama_model

    def analyze(self, content: str) -> JournalAnalysisResult:
        response = httpx.post(
            f"{self.base_url}/api/chat",
            json={
                "model": self.model_name,
                "messages": [
                    {
                        "role": "system",
                        "content": SYSTEM_PROMPT,
                    },
                    {
                        "role": "user",
                        "content": content,
                    },
                ],
                "format": JOURNAL_SIGNAL_EXTRACTION_SCHEMA,
                "stream": False,
                "options": {
                    "temperature": 0,
                },
            },
            timeout=120,
        )

        response.raise_for_status()

        body = response.json()

        raw_content = body["message"]["content"]

        try:
            parsed_output = json.loads(raw_content)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Ollama returned invalid JSON: {raw_content}") from exc

        try:
            cleaned_signals = []

            for signal in parsed_output.get("detected_signals", []):
                if signal.get("signal_code") not in ALLOWED_SIGNAL_CODES:
                    continue

            signal["confidence"] = min(signal.get("confidence", 0.0), 0.85)
            signal["value"] = max(0.0, min(1.0, signal.get("value", 0.0)))

            cleaned_signals.append(signal)

            cleaned_safety_flags = [
            safety_flag
            for safety_flag in parsed_output.get("safety_flags", [])
            if safety_flag in ALLOWED_SAFETY_FLAGS
                                ]

            return JournalAnalysisResult(
    detected_signals=cleaned_signals,
    safety_flags=cleaned_safety_flags,
    language=parsed_output.get("language"),
    provider=self.provider,
    model_name=self.model_name,
    prompt_version=self.prompt_version,
    )
        except ValidationError as exc:
            raise ValueError(f"Ollama output did not match schema: {parsed_output}") from exc