from dataclasses import dataclass, field
from typing import Any

from app.db.models.action_template import ActionTemplate


SEMANTIC_TAG_MATCH_WEIGHT = 1.0
NEED_MATCH_WEIGHT = 1.5
LIFE_DOMAIN_MATCH_WEIGHT = 0.75
GOAL_MATCH_WEIGHT = 1.25
COPING_STYLE_MATCH_WEIGHT = 0.75

MAX_SUGGESTION_CONFIDENCE = 0.95


@dataclass(frozen=True)
class GoalScoringContext:
    category: str
    priority: int
    confidence: float | None = None


@dataclass(frozen=True)
class ActionTemplateScoringContext:
    semantic_tags: set[str] = field(default_factory=set)
    needs: set[str] = field(default_factory=set)
    life_domains: set[str] = field(default_factory=set)

    semantic_dimensions: dict[str, float] = field(default_factory=dict)
    semantic_confidence: float | None = None

    goals: list[GoalScoringContext] = field(default_factory=list)
    coping_styles: set[str] = field(default_factory=set)

    current_state: dict[str, float] = field(default_factory=dict)
    state_confidence: float | None = None


@dataclass(frozen=True)
class ScoredActionTemplate:
    template: ActionTemplate
    score: float
    priority: int
    confidence: float
    matching_reasons: list[str]


def score_action_templates(
    templates: list[ActionTemplate],
    context: ActionTemplateScoringContext,
    maximum_results: int = 3,
) -> list[ScoredActionTemplate]:
    scored_templates: list[ScoredActionTemplate] = []

    for template in templates:
        scored_template = score_action_template(
            template=template,
            context=context,
        )

        if scored_template is None:
            continue

        scored_templates.append(scored_template)

    scored_templates.sort(
        key=lambda item: (
            item.score,
            item.priority,
            item.confidence,
            item.template.code,
        ),
        reverse=True,
    )

    return scored_templates[:maximum_results]


def score_action_template(
    template: ActionTemplate,
    context: ActionTemplateScoringContext,
) -> ScoredActionTemplate | None:
    score = 0.0
    reasons: list[str] = []
    evidence_confidences: list[float] = []

    semantic_tag_matches = _intersection(
        context.semantic_tags,
        template.match_semantic_tags_json,
    )

    if semantic_tag_matches:
        score += (
            len(semantic_tag_matches)
            * SEMANTIC_TAG_MATCH_WEIGHT
        )
        reasons.extend(
            f"semantic_tag:{value}"
            for value in sorted(semantic_tag_matches)
        )

        if context.semantic_confidence is not None:
            evidence_confidences.append(context.semantic_confidence)

    need_matches = _intersection(
        context.needs,
        template.match_needs_json,
    )

    if need_matches:
        score += len(need_matches) * NEED_MATCH_WEIGHT
        reasons.extend(
            f"need:{value}"
            for value in sorted(need_matches)
        )

        if context.semantic_confidence is not None:
            evidence_confidences.append(context.semantic_confidence)

    life_domain_matches = _intersection(
        context.life_domains,
        template.match_life_domains_json,
    )

    if life_domain_matches:
        score += (
            len(life_domain_matches)
            * LIFE_DOMAIN_MATCH_WEIGHT
        )
        reasons.extend(
            f"life_domain:{value}"
            for value in sorted(life_domain_matches)
        )

        if context.semantic_confidence is not None:
            evidence_confidences.append(context.semantic_confidence)

    template_goal_categories = _normalized_set(
        template.match_goal_categories_json
    )

    for goal in context.goals:
        if goal.category not in template_goal_categories:
            continue

        priority_factor = max(
            0.1,
            min(1.0, goal.priority / 10),
        )

        score += GOAL_MATCH_WEIGHT * priority_factor
        reasons.append(f"goal:{goal.category}")

        if goal.confidence is not None:
            evidence_confidences.append(
                _cap_score(goal.confidence)
            )

    coping_style_matches = _intersection(
        context.coping_styles,
        template.match_coping_styles_json,
    )

    if coping_style_matches:
        score += (
            len(coping_style_matches)
            * COPING_STYLE_MATCH_WEIGHT
        )
        reasons.extend(
            f"coping_style:{value}"
            for value in sorted(coping_style_matches)
        )

    for condition in template.conditions_json or []:
        matched_condition = _evaluate_condition(
            condition=condition,
            context=context,
        )

        if matched_condition is None:
            continue

        condition_weight, reason, confidence = matched_condition

        score += condition_weight
        reasons.append(reason)

        if confidence is not None:
            evidence_confidences.append(confidence)

    score = round(score, 4)

    if score < template.minimum_score:
        return None

    priority = _calculate_priority(
        base_priority=template.base_priority,
        score=score,
    )

    confidence = _calculate_confidence(
        base_confidence=template.base_confidence,
        evidence_confidences=evidence_confidences,
        score=score,
    )

    return ScoredActionTemplate(
        template=template,
        score=score,
        priority=priority,
        confidence=confidence,
        matching_reasons=reasons,
    )


def _evaluate_condition(
    condition: Any,
    context: ActionTemplateScoringContext,
) -> tuple[float, str, float | None] | None:
    if not isinstance(condition, dict):
        return None

    source = _normalize_token(condition.get("source"))
    dimension = _normalize_token(condition.get("dimension"))
    operator = _normalize_token(condition.get("operator"))

    threshold = _safe_float(condition.get("threshold"))
    weight = _safe_float(condition.get("weight"))

    if (
        source not in {"semantic", "state"}
        or not dimension
        or operator not in {"gte", "lte"}
        or threshold is None
        or weight is None
        or weight <= 0
    ):
        return None

    if source == "semantic":
        actual_value = context.semantic_dimensions.get(dimension)
        confidence = context.semantic_confidence
    else:
        actual_value = context.current_state.get(dimension)
        confidence = context.state_confidence

    if actual_value is None:
        return None

    if operator == "gte":
        matches = actual_value >= threshold
    else:
        matches = actual_value <= threshold

    if not matches:
        return None

    return (
        weight,
        (
            f"{source}_dimension:"
            f"{dimension}:{operator}:{threshold}"
        ),
        confidence,
    )


def _calculate_priority(
    base_priority: int,
    score: float,
) -> int:
    score_boost = min(
        3,
        int(score // 2),
    )

    return max(
        1,
        min(
            10,
            base_priority + score_boost,
        ),
    )


def _calculate_confidence(
    base_confidence: float,
    evidence_confidences: list[float],
    score: float,
) -> float:
    values = [
        _cap_score(base_confidence),
        *[
            _cap_score(value)
            for value in evidence_confidences
        ],
    ]

    evidence_confidence = sum(values) / len(values)

    score_boost = min(
        0.15,
        score * 0.02,
    )

    return round(
        min(
            MAX_SUGGESTION_CONFIDENCE,
            evidence_confidence + score_boost,
        ),
        4,
    )


def _intersection(
    context_values: set[str],
    template_values: Any,
) -> set[str]:
    return {
        _normalize_token(value)
        for value in context_values
        if _normalize_token(value)
    }.intersection(
        _normalized_set(template_values)
    )


def _normalized_set(
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


def _safe_float(
    value: Any,
) -> float | None:
    if value is None:
        return None

    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _cap_score(
    value: float,
) -> float:
    return max(
        0.0,
        min(1.0, value),
    )