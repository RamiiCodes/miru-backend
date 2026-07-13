from uuid import UUID

from app.db.models.user_goal import UserGoal


GOAL_CATEGORY_ACTION_MATCHES: dict[str, dict[str, list[str]]] = {
    "stress_management": {
    "primary": [
        "short_stress_pause",
        "reduce_scope_today",
        "post_work_decompression_note",
        ],
    "secondary": [
        "name_the_looping_thought",
        "choose_one_small_next_step",
        "work_trigger_note",
        ],
    },
    "sleep": {
        "primary": [
            "sleep_stress_wind_down",
        ],
        "secondary": [
            "short_stress_pause",
            "reduce_scope_today",
        ],
    },
    "emotional_awareness": {
        "primary": [
            "name_the_looping_thought",
            "two_column_thought_check",
            "work_trigger_note",
        ],
        "secondary": [
            "balanced_self_response",
        ],
    },
    "self_esteem": {
        "primary": [
            "balanced_self_response",
            "self_criticism_reframe",
        ],
        "secondary": [
            "two_column_thought_check",
        ],
    },
    "social_connection": {
        "primary": [
            "low_pressure_connection",
        ],
        "secondary": [
            "choose_one_small_next_step",
        ],
    },
    "work_life_balance": {
        "primary": [
            "post_work_decompression_note",
            "work_trigger_note",
            "reduce_scope_today",
        ],
        "secondary": [
            "short_stress_pause",
        ],
    },
    "grief_processing": {
        "primary": [
            "low_pressure_connection",
            "reduce_scope_today",
            "choose_one_small_next_step",
        ],
        "secondary": [
            "balanced_self_response",
            "short_stress_pause",
        ],
    },
    "habit_building": {
        "primary": [
            "choose_one_small_next_step",
        ],
        "secondary": [
            "reduce_scope_today",
        ],
    },
    "personal_growth": {
        "primary": [
            "choose_one_small_next_step",
            "two_column_thought_check",
        ],
        "secondary": [
            "name_the_looping_thought",
        ],
    },
    "mental_clarity": {
        "primary": [
            "name_the_looping_thought",
            "two_column_thought_check",
        ],
        "secondary": [
            "short_stress_pause",
        ],
    },
}


def apply_goal_adjustments(
    action_code: str,
    priority: int,
    confidence: float,
    user_goals: list[UserGoal],
) -> tuple[int, float]:
    active_goals = [
        goal
        for goal in user_goals
        if goal.status == "active"
    ]

    if not active_goals:
        return priority, confidence

    priority_bonus = 0
    confidence_bonus = 0.0

    for goal in active_goals:
        match_strength = _match_strength(
            goal_category=goal.category,
            action_code=action_code,
        )

        if match_strength == "none":
            continue

        if match_strength == "primary":
            priority_bonus += 2
            confidence_bonus += 0.12

        if match_strength == "secondary":
            priority_bonus += 1
            confidence_bonus += 0.06

        if goal.priority >= 8:
            priority_bonus += 1
            confidence_bonus += 0.03

    adjusted_priority = min(
        10,
        priority + min(priority_bonus, 3),
    )

    adjusted_confidence = round(
        min(
            0.95,
            confidence + min(confidence_bonus, 0.20),
        ),
        2,
    )

    return adjusted_priority, adjusted_confidence


def get_goal_alignment_ids(
    action_code: str,
    user_goals: list[UserGoal],
) -> list[UUID]:
    return [
        goal.id
        for goal in user_goals
        if goal.status == "active"
        and _match_strength(
            goal_category=goal.category,
            action_code=action_code,
        )
        != "none"
    ]


def _match_strength(
    goal_category: str,
    action_code: str,
) -> str:
    matches = GOAL_CATEGORY_ACTION_MATCHES.get(goal_category)

    if matches is None:
        return "none"

    if action_code in matches.get("primary", []):
        return "primary"

    if action_code in matches.get("secondary", []):
        return "secondary"

    return "none"
