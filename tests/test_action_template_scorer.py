from types import SimpleNamespace

from app.services.action_template_scorer import (
    ActionTemplateScoringContext,
    GoalScoringContext,
    score_action_templates,
)


def _template(
    code: str,
    *,
    tags=None,
    needs=None,
    domains=None,
    goals=None,
    coping_styles=None,
    conditions=None,
    minimum_score=1.0,
):
    return SimpleNamespace(
        code=code,
        title=code,
        content=code,
        match_semantic_tags_json=tags or [],
        match_needs_json=needs or [],
        match_life_domains_json=domains or [],
        match_goal_categories_json=goals or [],
        match_coping_styles_json=coping_styles or [],
        conditions_json=conditions or [],
        base_priority=5,
        base_confidence=0.5,
        minimum_score=minimum_score,
    )


def test_template_is_scored_by_open_ended_semantic_tags():
    templates = [
        _template(
            "generic_transition_support",
            tags=["unexpected_identity_shift"],
        )
    ]

    context = ActionTemplateScoringContext(
        semantic_tags={
            "unexpected_identity_shift",
        },
        semantic_confidence=0.9,
    )

    result = score_action_templates(
        templates=templates,
        context=context,
    )

    assert len(result) == 1
    assert result[0].template.code == (
        "generic_transition_support"
    )

    assert (
        "semantic_tag:unexpected_identity_shift"
        in result[0].matching_reasons
    )


def test_template_is_scored_by_need_without_action_code_mapping():
    templates = [
        _template(
            "grounding_template",
            needs=["grounding"],
        ),
        _template(
            "connection_template",
            needs=["connection"],
        ),
    ]

    context = ActionTemplateScoringContext(
        needs={"connection"},
        semantic_confidence=0.85,
    )

    result = score_action_templates(
        templates=templates,
        context=context,
    )

    assert len(result) == 1
    assert result[0].template.code == "connection_template"


def test_template_is_scored_by_goal_metadata_not_python_map():
    templates = [
        _template(
            "clarity_action",
            goals=["mental_clarity"],
        )
    ]

    context = ActionTemplateScoringContext(
        goals=[
            GoalScoringContext(
                category="mental_clarity",
                priority=9,
                confidence=0.8,
            )
        ]
    )

    result = score_action_templates(
        templates=templates,
        context=context,
    )

    assert len(result) == 1
    assert result[0].template.code == "clarity_action"


def test_generic_semantic_dimension_condition_is_supported():
    templates = [
        _template(
            "low_control_support",
            conditions=[
                {
                    "source": "semantic",
                    "dimension": "control",
                    "operator": "lte",
                    "threshold": 0.3,
                    "weight": 1.5,
                }
            ],
        )
    ]

    context = ActionTemplateScoringContext(
        semantic_dimensions={
            "control": 0.2,
        },
        semantic_confidence=0.9,
    )

    result = score_action_templates(
        templates=templates,
        context=context,
    )

    assert len(result) == 1
    assert result[0].template.code == (
        "low_control_support"
    )


def test_unmatched_templates_are_not_returned():
    templates = [
        _template(
            "connection_template",
            needs=["connection"],
        )
    ]

    context = ActionTemplateScoringContext(
        needs={"rest"},
        semantic_confidence=0.9,
    )

    result = score_action_templates(
        templates=templates,
        context=context,
    )

    assert result == []