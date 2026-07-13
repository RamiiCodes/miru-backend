import re
from typing import Any

from pydantic import BaseModel

from app.ai.journal_analyzer import JournalSemanticFrameResult


NORMALIZER_VERSION = "semantic_frame_normalizer_v0_1"

CORE_DIMENSION_NAMES = [
    "valence",
    "arousal",
    "threat",
    "control",
    "social_connection",
    "uncertainty",
    "self_evaluation",
    "energy",
]


class NormalizedJournalSemanticFrame(BaseModel):
    core_dimensions_json: dict[str, dict[str, Any] | None]
    emotion_labels_json: list[str]
    semantic_tags_json: list[str]
    life_domains_json: list[str]
    needs_json: list[str]
    additional_dimensions_json: list[dict[str, Any]]
    event_candidates_json: list[dict[str, Any]]
    safety_flags_json: list[str]
    overall_confidence: float | None
    raw_output_json: dict[str, Any]


def normalize_semantic_frame(
    semantic_frame: JournalSemanticFrameResult,
) -> NormalizedJournalSemanticFrame:
    """
    Normalize a JournalSemanticFrameResult before storage.

    This layer should clean and validate.
    It should not infer, expand, or invent new meaning.
    """

    return NormalizedJournalSemanticFrame(
        core_dimensions_json=_normalize_core_dimensions(
            semantic_frame.core_dimensions
        ),
        emotion_labels_json=_normalize_text_labels(
            semantic_frame.emotion_labels
        ),
        semantic_tags_json=_normalize_snake_case_list(
            semantic_frame.semantic_tags
        ),
        life_domains_json=_normalize_snake_case_list(
            semantic_frame.life_domains
        ),
        needs_json=_normalize_snake_case_list(
            semantic_frame.needs
        ),
        additional_dimensions_json=_normalize_additional_dimensions(
            semantic_frame.additional_dimensions
        ),
        event_candidates_json=_normalize_event_candidates(
            semantic_frame.event_candidates
        ),
        safety_flags_json=_normalize_snake_case_list(
            semantic_frame.safety_flags
        ),
        overall_confidence=_normalize_optional_score(
            semantic_frame.overall_confidence
        ),
        raw_output_json=_normalize_raw_output(
            semantic_frame.raw_output
        ),
    )


def _normalize_core_dimensions(
    core_dimensions: dict[str, Any],
) -> dict[str, dict[str, Any] | None]:
    normalized_dimensions: dict[str, dict[str, Any] | None] = {
        dimension_name: None
        for dimension_name in CORE_DIMENSION_NAMES
    }

    for raw_dimension_name, raw_dimension in core_dimensions.items():
        dimension_name = _normalize_snake_case(raw_dimension_name)

        if dimension_name not in normalized_dimensions:
            continue

        normalized_dimensions[dimension_name] = _normalize_dimension(
            raw_dimension
        )

    return normalized_dimensions


def _normalize_dimension(
    raw_dimension: Any,
) -> dict[str, Any] | None:
    value = _normalize_required_score(
        _get_value(raw_dimension, "value")
    )

    confidence = _normalize_required_score(
        _get_value(raw_dimension, "confidence")
    )

    if value is None or confidence is None:
        return None

    return {
        "value": value,
        "confidence": confidence,
        "evidence": _normalize_optional_text(
            _get_value(raw_dimension, "evidence")
        ),
        "reason": _normalize_optional_text(
            _get_value(raw_dimension, "reason")
        ),
    }


def _normalize_additional_dimensions(
    additional_dimensions: list[Any],
) -> list[dict[str, Any]]:
    normalized_dimensions: list[dict[str, Any]] = []

    for raw_dimension in additional_dimensions:
        name = _normalize_snake_case(
            _get_value(raw_dimension, "name")
        )

        if not name:
            continue

        normalized_dimension = _normalize_dimension(raw_dimension)

        if normalized_dimension is None:
            continue

        normalized_dimensions.append(
            {
                "name": name,
                **normalized_dimension,
            }
        )

    return _dedupe_dicts_by_key(
        values=normalized_dimensions,
        key="name",
    )


def _normalize_event_candidates(
    event_candidates: list[Any],
) -> list[dict[str, Any]]:
    normalized_candidates: list[dict[str, Any]] = []

    for raw_candidate in event_candidates:
        event_type = _normalize_snake_case(
            _get_value(raw_candidate, "event_type")
        )

        if not event_type:
            continue

        confidence = _normalize_required_score(
            _get_value(raw_candidate, "confidence")
        )

        if confidence is None:
            continue

        normalized_candidates.append(
            {
                "category": _normalize_optional_snake_case(
                    _get_value(raw_candidate, "category")
                ),
                "event_type": event_type,
                "title": _normalize_optional_text(
                    _get_value(raw_candidate, "title")
                ),
                "description": _normalize_optional_text(
                    _get_value(raw_candidate, "description")
                ),
                "significance": _normalize_optional_score(
                    _get_value(raw_candidate, "significance")
                ),
                "valence": _normalize_optional_score(
                    _get_value(raw_candidate, "valence")
                ),
                "confidence": confidence,
                "evidence": _normalize_optional_text(
                    _get_value(raw_candidate, "evidence")
                ),
                "semantic_tags": _normalize_snake_case_list(
                    _get_value(raw_candidate, "semantic_tags") or []
                ),
                "life_domains": _normalize_snake_case_list(
                    _get_value(raw_candidate, "life_domains") or []
                ),
            }
        )

    return _dedupe_event_candidates(normalized_candidates)


def _normalize_raw_output(
    raw_output: dict[str, Any],
) -> dict[str, Any]:
    if isinstance(raw_output, dict):
        return raw_output

    return {}


def _normalize_text_labels(
    values: list[str],
) -> list[str]:
    normalized_values: list[str] = []
    seen_values: set[str] = set()

    for value in values:
        if not isinstance(value, str):
            continue

        normalized_value = re.sub(
            r"\s+",
            " ",
            value.strip().lower(),
        )

        if not normalized_value:
            continue

        if normalized_value in seen_values:
            continue

        seen_values.add(normalized_value)
        normalized_values.append(normalized_value)

    return normalized_values


def _normalize_snake_case_list(
    values: list[str],
) -> list[str]:
    normalized_values: list[str] = []
    seen_values: set[str] = set()

    for value in values:
        normalized_value = _normalize_snake_case(value)

        if not normalized_value:
            continue

        if normalized_value in seen_values:
            continue

        seen_values.add(normalized_value)
        normalized_values.append(normalized_value)

    return normalized_values


def _normalize_optional_snake_case(
    value: Any,
) -> str | None:
    normalized_value = _normalize_snake_case(value)

    if not normalized_value:
        return None

    return normalized_value


def _normalize_snake_case(
    value: Any,
) -> str:
    if not isinstance(value, str):
        return ""

    normalized_value = value.strip().lower()
    normalized_value = normalized_value.replace("&", " and ")
    normalized_value = re.sub(r"[^a-z0-9]+", "_", normalized_value)
    normalized_value = re.sub(r"_+", "_", normalized_value)

    return normalized_value.strip("_")


def _normalize_required_score(
    value: Any,
) -> float | None:
    parsed_value = _parse_float(value)

    if parsed_value is None:
        return None

    return _cap_score(parsed_value)


def _normalize_optional_score(
    value: Any,
) -> float | None:
    parsed_value = _parse_float(value)

    if parsed_value is None:
        return None

    return _cap_score(parsed_value)


def _cap_score(
    value: float,
) -> float:
    return round(
        max(0.0, min(1.0, value)),
        4,
    )


def _parse_float(
    value: Any,
) -> float | None:
    if value is None:
        return None

    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _normalize_optional_text(
    value: Any,
) -> str | None:
    if value is None:
        return None

    if not isinstance(value, str):
        return None

    normalized_value = re.sub(
        r"\s+",
        " ",
        value.strip(),
    )

    if not normalized_value:
        return None

    return normalized_value


def _get_value(
    value: Any,
    field_name: str,
) -> Any:
    if isinstance(value, dict):
        return value.get(field_name)

    return getattr(value, field_name, None)


def _dedupe_dicts_by_key(
    values: list[dict[str, Any]],
    key: str,
) -> list[dict[str, Any]]:
    seen_values: set[Any] = set()
    deduped_values: list[dict[str, Any]] = []

    for value in values:
        key_value = value.get(key)

        if key_value in seen_values:
            continue

        seen_values.add(key_value)
        deduped_values.append(value)

    return deduped_values


def _dedupe_event_candidates(
    values: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    seen_values: set[tuple[str | None, str, str | None]] = set()
    deduped_values: list[dict[str, Any]] = []

    for value in values:
        dedupe_key = (
            value.get("category"),
            value["event_type"],
            value.get("evidence"),
        )

        if dedupe_key in seen_values:
            continue

        seen_values.add(dedupe_key)
        deduped_values.append(value)

    return deduped_values