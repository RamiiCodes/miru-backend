import json
from uuid import UUID

from sqlalchemy.orm import Session

from app.db.models.action_suggestion import ActionSuggestion
from app.db.repositories.action_suggestion_repository import (
    create_action_suggestion,
    get_active_action_suggestion_by_code,
)
from app.db.repositories.current_emotional_state_repository import (
    get_latest_current_emotional_state,
)
from app.db.repositories.user_coping_style_repository import (
    get_user_coping_style_by_user_id,
)
from app.db.repositories.user_goal_repository import (
    list_reasoning_user_goals_by_user_id,
)
from app.db.repositories.action_template_repository import (
    list_active_action_templates,
)
from app.db.repositories.journal_semantic_frame_repository import (
    get_latest_journal_semantic_frame_for_user,
)
from app.services.action_template_context_builder import (
    build_action_template_scoring_context,
)
from app.services.action_template_scorer import (
    score_action_templates,
)


def _priority_label_from_score(priority_score: int) -> str:
    if priority_score >= 7:
        return "high"

    if priority_score >= 4:
        return "medium"

    return "low"


def _template_snapshot_reason(
    scored_template,
    semantic_frame,
    user_goals,
    current_state,
) -> str:
    template = scored_template.template

    return json.dumps(
        {
            "ranking_version": "action_template_scorer_v0_1",
            "action_template_id": str(template.id),
            "action_template_version": template.version,
            "template_score": scored_template.score,
            "matching_reasons": scored_template.matching_reasons,
            "semantic_frame_id": (
                str(semantic_frame.id)
                if semantic_frame is not None
                else None
            ),
            "user_goal_ids": [
                str(goal.id)
                for goal in user_goals
                if getattr(goal, "status", None) == "active"
            ],
            "current_state_id": (
                str(current_state.id)
                if current_state is not None
                else None
            ),
        },
        sort_keys=True,
    )


def generate_action_suggestions_for_user(
    db: Session,
    user_id: UUID,
) -> list[ActionSuggestion]:
    state = get_latest_current_emotional_state(db=db, user_id=user_id)

    user_goals = list_reasoning_user_goals_by_user_id(
        db=db,
        user_id=user_id,
    )

    coping_style = get_user_coping_style_by_user_id(
        db=db,
        user_id=user_id,
    )
    coping_styles = [coping_style] if coping_style is not None else []

    semantic_frame = get_latest_journal_semantic_frame_for_user(
        db=db,
        user_id=user_id,
    )

    action_templates = list_active_action_templates(
        db=db,
    )

    if not action_templates:
        return []

    scoring_context = build_action_template_scoring_context(
        semantic_frame=semantic_frame,
        user_goals=user_goals,
        coping_styles=coping_styles,
        current_state=state,
    )

    scored_templates = score_action_templates(
        templates=action_templates,
        context=scoring_context,
        maximum_results=3,
    )

    created_template_actions: list[ActionSuggestion] = []

    for scored_template in scored_templates:
        template = scored_template.template

        existing_suggestion = get_active_action_suggestion_by_code(
            db=db,
            user_id=user_id,
            action_code=template.code,
        )

        if existing_suggestion is not None:
            continue

        created_template_action = create_action_suggestion(
            db=db,
            user_id=user_id,
            action_code=template.code,
            title=template.title,
            description=template.content,
            action_type=template.action_type or "template",
            priority=_priority_label_from_score(scored_template.priority),
            confidence=scored_template.confidence,
            reason=_template_snapshot_reason(
                scored_template=scored_template,
                semantic_frame=semantic_frame,
                user_goals=user_goals,
                current_state=state,
            ),
            source_type="action_template",
            source_id=template.id,
        )

        created_template_actions.append(created_template_action)

    return created_template_actions
