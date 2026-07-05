from uuid import UUID

from sqlalchemy.orm import Session

from app.db.models.action_suggestion import ActionSuggestion
from app.db.repositories.action_suggestion_repository import create_action_suggestion
from app.db.repositories.basic_insight_repository import list_basic_insights_by_user_id
from app.db.repositories.current_emotional_state_repository import (
    get_latest_current_emotional_state,
)
from app.db.repositories.pattern_detection_repository import (
    list_pattern_detections_by_user_id,
)


def generate_action_suggestions_for_user(
    db: Session,
    user_id: UUID,
) -> list[ActionSuggestion]:
    state = get_latest_current_emotional_state(db=db, user_id=user_id)
    insights = list_basic_insights_by_user_id(db=db, user_id=user_id)
    patterns = list_pattern_detections_by_user_id(db=db, user_id=user_id)

    actions_to_create: list[dict] = []
    seen_action_codes: set[str] = set()

    def add_action(action_data: dict) -> None:
        action_code = action_data["action_code"]

        # Avoid showing the same practical action twice in one generation pass.
        if action_code in seen_action_codes:
            return

        seen_action_codes.add(action_code)
        actions_to_create.append(action_data)

    for pattern in patterns:
        if pattern.pattern_code == "repeated_work_stress":
            add_action(
                {
                    "action_code": "post_work_decompression_note",
                    "title": "Try a short post-work decompression note",
                    "description": (
                        "After work, you could take 5 minutes to write what is still "
                        "looping in your mind. Keep it simple: what happened, what you "
                        "felt, and what can wait until tomorrow."
                    ),
                    "action_type": "reflection",
                    "priority": "high" if pattern.severity == "high" else "medium",
                    "reason": "Miru detected repeated work-related stress across multiple days.",
                    "source_type": "pattern_detection",
                    "source_id": pattern.id,
                    "confidence": 0.72,
                }
            )

        if pattern.pattern_code == "repeated_rumination":
            add_action(
                {
                    "action_code": "name_the_looping_thought",
                    "title": "Name the looping thought",
                    "description": (
                        "You could write down the repeated thought in one sentence, then "
                        "label it as fact, fear, assumption, or something to verify later."
                    ),
                    "action_type": "cognitive_reflection",
                    "priority": "medium",
                    "reason": "Miru detected rumination signals on multiple days.",
                    "source_type": "pattern_detection",
                    "source_id": pattern.id,
                    "confidence": 0.68,
                }
            )

        if pattern.pattern_code == "repeated_self_criticism":
            add_action(
                {
                    "action_code": "balanced_self_response",
                    "title": "Write a more balanced response",
                    "description": (
                        "When a self-critical sentence appears, you could write one more "
                        "balanced alternative sentence. For example: what would you say to "
                        "a friend in the same situation?"
                    ),
                    "action_type": "self_reflection",
                    "priority": "medium",
                    "reason": "Miru detected repeated self-critical language.",
                    "source_type": "pattern_detection",
                    "source_id": pattern.id,
                    "confidence": 0.66,
                }
            )

        if pattern.pattern_code == "low_sleep_high_stress":
            add_action(
                {
                    "action_code": "sleep_stress_wind_down",
                    "title": "Try a small wind-down checkpoint",
                    "description": (
                        "Before sleep, you could write one stress trigger and one thing "
                        "that can wait until tomorrow. Keep it short and low effort."
                    ),
                    "action_type": "sleep_support",
                    "priority": "medium",
                    "reason": "Miru detected lower sleep quality together with elevated stress.",
                    "source_type": "pattern_detection",
                    "source_id": pattern.id,
                    "confidence": 0.64,
                }
            )

    for insight in insights:
        if insight.rule_code == "stress_rumination_connection":
            add_action(
                {
                    "action_code": "two_column_thought_check",
                    "title": "Separate facts from interpretations",
                    "description": (
                        "You could make two quick columns: what actually happened, and "
                        "what your mind is adding or predicting. This may help clarify "
                        "what is certain and what is still uncertain."
                    ),
                    "action_type": "cognitive_reflection",
                    "priority": "medium",
                    "reason": "Miru detected a possible link between stress and repetitive thinking.",
                    "source_type": "basic_insight",
                    "source_id": insight.id,
                    "confidence": 0.66,
                }
            )

        if insight.rule_code == "self_criticism_self_esteem_connection":
            add_action(
                {
                    "action_code": "self_criticism_reframe",
                    "title": "Reframe one self-critical sentence",
                    "description": (
                        "Pick one harsh sentence from your thoughts and rewrite it in a "
                        "more precise, less absolute way. For example, replace 'I am bad' "
                        "with 'I struggled with this situation today.'"
                    ),
                    "action_type": "self_reflection",
                    "priority": "medium",
                    "reason": "Miru detected self-critical language that may be linked to self-esteem.",
                    "source_type": "basic_insight",
                    "source_id": insight.id,
                    "confidence": 0.65,
                }
            )

        if insight.rule_code == "fear_failure_motivation_connection":
            add_action(
                {
                    "action_code": "choose_one_small_next_step",
                    "title": "Choose one small next step",
                    "description": (
                        "You could choose one very small action that takes less than "
                        "10 minutes. The goal is not to solve everything, only to restart "
                        "movement gently."
                    ),
                    "action_type": "planning",
                    "priority": "medium",
                    "reason": "Miru detected that fear of failure may be lowering motivation.",
                    "source_type": "basic_insight",
                    "source_id": insight.id,
                    "confidence": 0.64,
                }
            )

        if insight.rule_code == "work_context_stress_connection":
            add_action(
                {
                    "action_code": "work_trigger_note",
                    "title": "Note the work trigger",
                    "description": (
                        "You could write the exact work moment that affected you today: "
                        "who was involved, what happened, and what emotion appeared first."
                    ),
                    "action_type": "reflection",
                    "priority": "medium",
                    "reason": "Miru detected that work context may be influencing stress.",
                    "source_type": "basic_insight",
                    "source_id": insight.id,
                    "confidence": 0.62,
                }
            )

    if state is not None:
        if state.stress_level is not None and state.stress_level >= 0.8:
            add_action(
                {
                    "action_code": "short_stress_pause",
                    "title": "Take a short stress pause",
                    "description": (
                        "You could take 2 minutes to pause, breathe slowly, and rate your "
                        "body tension from 0 to 10. This is only a check-in, not a fix."
                    ),
                    "action_type": "grounding",
                    "priority": "high",
                    "reason": "Your current stress level is elevated.",
                    "source_type": "current_emotional_state",
                    "source_id": state.id,
                    "confidence": 0.7,
                }
            )

        if (
            state.energy_level is not None
            and state.energy_level <= 0.4
            and state.sleep_quality is not None
            and state.sleep_quality <= 0.5
        ):
            add_action(
                {
                    "action_code": "reduce_scope_today",
                    "title": "Reduce the scope for today",
                    "description": (
                        "Your energy and sleep signals are low. You could pick one "
                        "essential task and postpone non-urgent tasks where possible."
                    ),
                    "action_type": "planning",
                    "priority": "medium",
                    "reason": "Your current state shows lower energy and lower sleep quality.",
                    "source_type": "current_emotional_state",
                    "source_id": state.id,
                    "confidence": 0.63,
                }
            )

        if (
            state.social_connection is not None
            and state.social_connection <= 0.4
        ):
            add_action(
                {
                    "action_code": "low_pressure_connection",
                    "title": "Try one low-pressure connection",
                    "description": (
                        "You could send a simple message to someone safe, without needing "
                        "to explain everything. A small connection can be enough."
                    ),
                    "action_type": "social_connection",
                    "priority": "low",
                    "reason": "Your current social connection signal is low.",
                    "source_type": "current_emotional_state",
                    "source_id": state.id,
                    "confidence": 0.6,
                }
            )

    created_actions: list[ActionSuggestion] = []

    for action_data in actions_to_create:
        created_action = create_action_suggestion(
            db=db,
            user_id=user_id,
            action_code=action_data["action_code"],
            title=action_data["title"],
            description=action_data["description"],
            action_type=action_data["action_type"],
            priority=action_data["priority"],
            reason=action_data["reason"],
            source_type=action_data["source_type"],
            source_id=action_data["source_id"],
            confidence=action_data["confidence"],
        )

        created_actions.append(created_action)

    return created_actions