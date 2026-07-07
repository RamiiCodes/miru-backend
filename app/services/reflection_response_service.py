from uuid import UUID

from sqlalchemy.orm import Session

from app.db.models.action_suggestion import ActionSuggestion
from app.db.models.reflection_response import ReflectionResponse
from app.db.repositories.action_suggestion_repository import (
    list_action_suggestions_by_user_id,
)
from app.db.repositories.basic_insight_repository import list_basic_insights_by_user_id
from app.db.repositories.current_emotional_state_repository import (
    get_latest_current_emotional_state,
)
from app.db.repositories.pattern_detection_repository import (
    list_pattern_detections_by_user_id,
)
from app.db.repositories.reflection_response_repository import (
    create_reflection_response,
)
from app.db.repositories.user_feedback_repository import list_user_feedback_by_user_id
from app.db.repositories.user_profile_repository import get_user_profile_by_user_id
from app.db.repositories.safety_event_repository import list_open_safety_events_by_user_id


PRIORITY_ORDER = {
    "high": 3,
    "medium": 2,
    "low": 1,
}


def _level_label(value: float | None) -> str:
    if value is None:
        return "unknown"

    if value >= 0.75:
        return "elevated"

    if value >= 0.45:
        return "moderate"

    return "lower"


def _select_tone(db: Session, user_id: UUID) -> str:
    profile = get_user_profile_by_user_id(db=db, user_id=user_id)

    if profile is not None:
        tone = profile.preferred_reflection_style

        if tone in {"balanced", "direct", "gentle", "detailed"}:
            return tone

    feedback = list_user_feedback_by_user_id(db=db, user_id=user_id)
    recent_ratings = [item.rating for item in feedback[:10]]

    if "too_direct" in recent_ratings:
        return "gentle"

    if "too_vague" in recent_ratings:
        return "direct"

    return "balanced"


def _select_top_action(actions: list[ActionSuggestion]) -> ActionSuggestion | None:
    active_actions = [
        action
        for action in actions
        if not action.is_completed and not action.is_dismissed
    ]

    if not active_actions:
        return None

    sorted_actions = sorted(
        active_actions,
        key=lambda action: (
            PRIORITY_ORDER.get(action.priority, 0),
            action.created_at,
        ),
        reverse=True,
    )

    return sorted_actions[0]


def _build_title(tone: str, stress_level: float | None, has_work_insight: bool) -> str:
    if has_work_insight:
        return "Reflection on work-related stress"

    if stress_level is not None and stress_level >= 0.75:
        return "Reflection on elevated stress"

    if tone == "gentle":
        return "A gentle reflection"

    if tone == "direct":
        return "Direct reflection"

    return "Current reflection"


def _build_message(
    tone: str,
    stress_level: float | None,
    energy_level: float | None,
    sleep_quality: float | None,
    motivation: float | None,
    self_esteem: float | None,
    insight_titles: list[str],
    pattern_titles: list[str],
    top_action: ActionSuggestion | None,
) -> str:
    stress_label = _level_label(stress_level)
    energy_label = _level_label(energy_level)
    sleep_label = _level_label(sleep_quality)

    if tone == "direct":
        opening = "Direct reflection: Miru sees a few signals worth noticing."
    elif tone == "gentle":
        opening = "A gentle observation: there may be a few things worth noticing today."
    elif tone == "detailed":
        opening = "Detailed reflection: Miru is combining your current state, recent insights, patterns, and available actions."
    else:
        opening = "Miru’s current reflection: a few signals may be worth noticing."

    state_sentence = (
        f"Your stress appears {stress_label}, energy appears {energy_label}, "
        f"and sleep quality appears {sleep_label}."
    )

    extra_state_notes = []

    if motivation is not None and motivation <= 0.4:
        extra_state_notes.append("Motivation may be lower than usual.")

    if self_esteem is not None and self_esteem <= 0.4:
        extra_state_notes.append("Self-critical signals may be affecting your self-perception.")

    if insight_titles:
        insight_sentence = "Recent insights point to: " + "; ".join(insight_titles[:3]) + "."
    else:
        insight_sentence = "There are no strong recent insights yet."

    if pattern_titles:
        pattern_sentence = "Recent repeated patterns include: " + "; ".join(pattern_titles[:3]) + "."
    else:
        pattern_sentence = "No repeated multi-day pattern is currently active."

    if top_action is not None:
        action_sentence = (
            f"A small next step you could try: {top_action.title}. "
            f"{top_action.description}"
        )
    else:
        action_sentence = (
            "A useful next step may simply be to add a short check-in or journal entry "
            "so Miru can understand the current context better."
        )

    safety_sentence = (
        "This is a reflection, not a diagnosis or medical advice."
    )

    parts = [
        opening,
        state_sentence,
        *extra_state_notes,
        insight_sentence,
        pattern_sentence,
        action_sentence,
        safety_sentence,
    ]

    return " ".join(parts)

def _build_safety_first_message(
        tone: str,
        flag_types: list[str]
) -> str:
    if tone == "direct":
        opening = (
            "Direct safety check-in: this entry may be heavier than a normal reflection."
        )
    elif tone == "gentle":
        opening = (
            "A gentle safety check-in: this may be a moment that deserves extra support."
        )
    elif tone == "detailed":
        opening = (
            "Detailed safety check-in: Miru detected safety-related signals and is prioritizing support over normal advice."
        )
    else:
        opening = (
            "Safety check-in: this may be more than a normal daily reflection."
        )

    flags_text = ", ".join(flag_types)

    return (
        f"{opening} "
        f"Detected safety signal(s): {flags_text}. "
        "Miru is not a crisis service and this is not a diagnosis. "
        "If you feel at risk right now, contact local emergency services or reach out to someone you trust. "
        "For now, the safest next step is to pause, avoid staying alone with the situation if possible, "
        "and seek real human support."
    )

def generate_reflection_response_for_user(
    db: Session,
    user_id: UUID,
) -> ReflectionResponse:
    state = get_latest_current_emotional_state(db=db, user_id=user_id)
    insights = list_basic_insights_by_user_id(db=db, user_id=user_id)
    patterns = list_pattern_detections_by_user_id(db=db, user_id=user_id)
    actions = list_action_suggestions_by_user_id(
        db=db,
        user_id=user_id,
        include_completed=False,
        include_dismissed=False,
    )

    tone = _select_tone(db=db, user_id=user_id)

    open_safety_events = list_open_safety_events_by_user_id(
        db=db,
        user_id=user_id,
    )

    if open_safety_events:
        flag_types = sorted({event.flag_type for event in open_safety_events})

        return create_reflection_response(
            db=db,
            user_id=user_id,
            source_type="manual",
            source_id=None,
            title="Safety check-in",
            message=_build_safety_first_message(
                tone=tone,
                flag_types=flag_types,
            ),
            tone=tone,
            response_type="gentle_checkin",
            suggested_action_id=None,
            source_snapshot_json={
                "safety_event_ids": [
                    str(event.id) for event in open_safety_events
                ],
                "safety_flag_types": flag_types,
                "tone_source": tone,
            },
        )

    latest_insights = insights[:3]
    latest_patterns = patterns[:3]
    top_action = _select_top_action(actions)

    insight_titles = [insight.title for insight in latest_insights]
    pattern_titles = [pattern.title for pattern in latest_patterns]

    has_work_insight = any(
        insight.rule_code == "work_context_stress_connection"
        for insight in latest_insights
    )

    title = _build_title(
        tone=tone,
        stress_level=state.stress_level if state else None,
        has_work_insight=has_work_insight,
    )

    message = _build_message(
        tone=tone,
        stress_level=state.stress_level if state else None,
        energy_level=state.energy_level if state else None,
        sleep_quality=state.sleep_quality if state else None,
        motivation=state.motivation if state else None,
        self_esteem=state.self_esteem if state else None,
        insight_titles=insight_titles,
        pattern_titles=pattern_titles,
        top_action=top_action,
    )

    if top_action is not None:
        response_type = "action_oriented"
    elif state is not None:
        response_type = "supportive_reflection"
    else:
        response_type = "gentle_checkin"

    source_type = "current_emotional_state" if state is not None else "manual"
    source_id = state.id if state is not None else None

    source_snapshot_json = {
        "state_id": str(state.id) if state else None,
        "insight_ids": [str(insight.id) for insight in latest_insights],
        "pattern_ids": [str(pattern.id) for pattern in latest_patterns],
        "suggested_action_id": str(top_action.id) if top_action else None,
        "tone_source": tone,
    }

    return create_reflection_response(
        db=db,
        user_id=user_id,
        source_type=source_type,
        source_id=source_id,
        title=title,
        message=message,
        tone=tone,
        response_type=response_type,
        suggested_action_id=top_action.id if top_action else None,
        source_snapshot_json=source_snapshot_json,
    )