from typing import Any

from app.db.models.journal_semantic_frame import JournalSemanticFrame
from app.services.action_template_scorer import (
    ActionTemplateScoringContext,
    GoalScoringContext,
)


CURRENT_STATE_FIELDS = [
    "stress_level",
    "energy_level",
    "sleep_quality",
    "social_connection",
    "emotional_stability",
    "motivation",
    "self_esteem",
    "physical_activity",
    "eating_habits",
]


def build_action_template_scoring_context(
    semantic_frame: JournalSemanticFrame | None,
    user_goals: list[Any],
    coping_styles: list[Any],
    current_state: Any | None,
) -> ActionTemplateScoringContext:
    return ActionTemplateScoringContext(
        semantic_tags=_string_set(
            getattr(
                semantic_frame,
                "semantic_tags_json",
                [],
            )
            if semantic_frame is not None
            else []
        ),
        needs=_string_set(
            getattr(
                semantic_frame,
                "needs_json",
                [],
            )
            if semantic_frame is not None
            else []
        ),
        life_domains=_string_set(
            getattr(
                semantic_frame,
                "life_domains_json",
                [],
            )
            if semantic_frame is not None
            else []
        ),
        semantic_dimensions=_semantic_dimensions(
            semantic_frame
        ),
        semantic_confidence=_safe_score(
            getattr(
                semantic_frame,
                "overall_confidence",
                None,
            )
        ),
        goals=_goal_contexts(user_goals),
        coping_styles=_coping_style_values(coping_styles),
        current_state=_current_state_values(current_state),
        state_confidence=_safe_score(
            getattr(current_state, "state_confidence", None)
            or getattr(current_state, "confidence", None)
            if current_state is not None
            else None
        ),
    )


def _semantic_dimensions(
    semantic_frame: JournalSemanticFrame | None,
) -> dict[str, float]:
    if semantic_frame is None:
        return {}

    core_dimensions = (
        semantic_frame.core_dimensions_json
        or {}
    )

    normalized_dimensions: dict[str, float] = {}

    for dimension_name, dimension_value in core_dimensions.items():
        if not isinstance(dimension_value, dict):
            continue

        value = _safe_score(
            dimension_value.get("value")
        )

        if value is None:
            continue

        normalized_dimensions[
            _normalize_token(dimension_name)
        ] = value

    return normalized_dimensions


def _goal_contexts(
    user_goals: list[Any],
) -> list[GoalScoringContext]:
    goal_contexts: list[GoalScoringContext] = []

    for goal in user_goals:
        status = _normalize_token(
            getattr(goal, "status", "")
        )

        if status != "active":
            continue

        category = _normalize_token(
            getattr(goal, "category", "")
        )

        if not category:
            continue

        priority = getattr(goal, "priority", 5)

        try:
            parsed_priority = int(priority)
        except (TypeError, ValueError):
            parsed_priority = 5

        goal_contexts.append(
            GoalScoringContext(
                category=category,
                priority=max(
                    1,
                    min(10, parsed_priority),
                ),
                confidence=_safe_score(
                    getattr(goal, "confidence", None)
                ),
            )
        )

    return goal_contexts


def _coping_style_values(
    coping_styles: list[Any],
) -> set[str]:
    values: set[str] = set()

    for coping_style in coping_styles:
        preferred_values = getattr(
            coping_style,
            "preferred_coping_styles",
            None,
        )

        if isinstance(preferred_values, list):
            for preferred_value in preferred_values:
                normalized_preferred_value = _normalize_token(
                    preferred_value,
                )

                if normalized_preferred_value:
                    values.add(normalized_preferred_value)

        raw_value = (
            getattr(coping_style, "coping_style", None)
            or getattr(coping_style, "style", None)
            or getattr(coping_style, "code", None)
        )

        normalized_value = _normalize_token(raw_value)

        if normalized_value:
            values.add(normalized_value)

    return values


def _current_state_values(
    current_state: Any | None,
) -> dict[str, float]:
    if current_state is None:
        return {}

    values: dict[str, float] = {}

    for field_name in CURRENT_STATE_FIELDS:
        value = _safe_score(
            getattr(current_state, field_name, None)
        )

        if value is not None:
            values[field_name] = value

    return values


def _string_set(
    values: Any,
) -> set[str]:
    if not isinstance(values, list):
        return set()

    return {
        normalized_value
        for value in values
        if (normalized_value := _normalize_token(value))
    }


def _normalize_token(
    value: Any,
) -> str:
    if not isinstance(value, str):
        return ""

    return (
        value.strip()
        .lower()
        .replace("-", "_")
        .replace(" ", "_")
    )


def _safe_score(
    value: Any,
) -> float | None:
    if value is None:
        return None

    try:
        parsed_value = float(value)
    except (TypeError, ValueError):
        return None

    return max(
        0.0,
        min(1.0, parsed_value),
    )
