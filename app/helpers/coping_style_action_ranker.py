from app.db.models.action_suggestion import ActionSuggestion
from app.db.models.user_coping_style import UserCopingStyle


ACTION_COPING_STYLE_MAP = {
    "post_work_decompression_note": "writing",
    "name_the_looping_thought": "writing",
    "balanced_self_response": "reflection",
    "sleep_stress_wind_down": "rest",
    "two_column_thought_check": "structure",
    "self_criticism_reframe": "reflection",
    "choose_one_small_next_step": "structure",
    "work_trigger_note": "writing",
    "short_stress_pause": "breathing",
    "reduce_scope_today": "structure",
    "low_pressure_connection": "social_support",
}


COPING_STYLE_SCORE_FIELDS = {
    "writing": "writing_preference_score",
    "movement": "movement_preference_score",
    "breathing": "breathing_preference_score",
    "social_support": "social_support_preference_score",
    "reflection": "reflection_preference_score",
    "structure": "structure_preference_score",
}


PRIORITY_ORDER = {
    "low": 1,
    "medium": 2,
    "high": 3,
}


REVERSE_PRIORITY_ORDER = {
    1: "low",
    2: "medium",
    3: "high",
}


def get_action_coping_style(action_code: str) -> str | None:
    return ACTION_COPING_STYLE_MAP.get(action_code)


def calculate_coping_match_score(
    action_code: str,
    coping_style: UserCopingStyle | None,
) -> float:
    if coping_style is None:
        return 0.0

    action_style = get_action_coping_style(action_code)

    if action_style is None:
        return 0.0

    disliked_styles = coping_style.disliked_coping_styles or []
    preferred_styles = coping_style.preferred_coping_styles or []

    if action_style in disliked_styles:
        return -0.30

    if action_style in preferred_styles:
        return 0.20

    score_field = COPING_STYLE_SCORE_FIELDS.get(action_style)

    if score_field is None:
        return 0.0

    preference_score = getattr(coping_style, score_field)

    if preference_score >= 8:
        return 0.20

    if preference_score >= 6:
        return 0.10

    if preference_score <= 2:
        return -0.25

    if preference_score <= 4:
        return -0.10

    return 0.0


def adjust_priority_for_coping_style(
    priority: str,
    coping_match_score: float,
) -> str:
    current_priority_value = PRIORITY_ORDER.get(priority, 2)

    if coping_match_score >= 0.20:
        current_priority_value += 1

    if coping_match_score <= -0.25:
        current_priority_value -= 1

    current_priority_value = max(1, min(3, current_priority_value))

    return REVERSE_PRIORITY_ORDER[current_priority_value]


def adjust_confidence_for_coping_style(
    confidence: float,
    coping_match_score: float,
) -> float:
    adjusted_confidence = confidence + coping_match_score

    return max(0.1, min(0.95, adjusted_confidence))


def rank_actions_by_coping_style(
    actions: list[ActionSuggestion],
    coping_style: UserCopingStyle | None,
) -> list[ActionSuggestion]:
    return sorted(
        actions,
        key=lambda action: (
            calculate_coping_match_score(
                action_code=action.action_code,
                coping_style=coping_style,
            ),
            PRIORITY_ORDER.get(action.priority, 0),
            action.created_at,
        ),
        reverse=True,
    )