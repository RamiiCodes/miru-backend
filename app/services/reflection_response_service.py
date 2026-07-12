from uuid import UUID

from sqlalchemy.orm import Session

from app.db.models.action_suggestion import ActionSuggestion
from app.db.models.reflection_response import ReflectionResponse
from app.db.models.user_context import UserContext
from app.db.repositories.reflection_response_repository import (
    create_reflection_response,
)
from app.helpers.reasoning_input_assembler import (
    ReasoningInputs,
    assemble_reasoning_inputs,
)
from app.helpers.coping_style_action_ranker import rank_actions_by_coping_style

PRIORITY_ORDER = {
    "high": 3,
    "medium": 2,
    "low": 1,
}

def _build_life_event_note(life_events) -> str | None:
    if not life_events:
        return None

    high_impact_events = [
        event
        for event in life_events
        if (
            event.emotional_impact is not None
            and event.emotional_impact >= 7
        )
        or event.category in ["family", "trauma", "health"]
    ]

    selected_event = high_impact_events[0] if high_impact_events else life_events[0]

    return (
        "Life context note: The user has confirmed an important life event: "
        f"{selected_event.title}. Use this only as gentle context. "
        "Do not make causal claims or diagnoses."
    )

def _level_label(value: float | None) -> str:
    if value is None:
        return "unknown"

    if value >= 0.75:
        return "elevated"

    if value >= 0.45:
        return "moderate"

    return "lower"


def _select_tone(reasoning_inputs: ReasoningInputs) -> str:
    profile = reasoning_inputs.profile

    if profile is not None:
        tone = profile.preferred_reflection_style

        if tone in {"balanced", "direct", "gentle", "detailed"}:
            return tone

    recent_ratings = [
        feedback.rating
        for feedback in reasoning_inputs.latest_feedback
    ]

    if "too_direct" in recent_ratings:
        return "gentle"

    if "too_vague" in recent_ratings:
        return "direct"

    return "balanced"


def _select_top_action(
    actions: list[ActionSuggestion],
    coping_style,
) -> ActionSuggestion | None:
    active_actions = [
        action
        for action in actions
        if not action.is_completed and not action.is_dismissed
    ]

    if not active_actions:
        return None

    ranked_actions = rank_actions_by_coping_style(
        actions=active_actions,
        coping_style=coping_style,
    )

    return ranked_actions[0]


def _build_title(
    tone: str,
    stress_level: float | None,
    has_work_insight: bool,
) -> str:
    if has_work_insight:
        return "Reflection on work-related stress"

    if stress_level is not None and stress_level >= 0.75:
        return "Reflection on elevated stress"

    if tone == "gentle":
        return "A gentle reflection"

    if tone == "direct":
        return "Direct reflection"

    return "Current reflection"


def _build_user_context_note(user_context: UserContext | None) -> str:
    if user_context is None:
        return (
            "Context note: Miru does not have your stable life context yet, so this "
            "reflection uses only recent check-ins, journal entries, and detected patterns."
        )

    notes: list[str] = []

    if user_context.work_stress_baseline >= 7:
        notes.append(
            "Your usual work stress baseline is high, so work-related signals are interpreted against an already demanding baseline."
        )
    elif user_context.work_stress_baseline <= 3:
        notes.append(
            "Your usual work stress baseline is low, so elevated work stress may stand out more strongly than usual."
        )

    if user_context.family_support_score <= 3:
        notes.append(
            "Family support is declared as limited, so Miru should not assume family is the easiest support source."
        )

    if user_context.social_connection_score <= 3:
        notes.append(
            "Social connection is declared as limited, so low-social-energy moments may need gentler recommendations."
        )
    elif user_context.social_connection_score >= 7:
        notes.append(
            "Social connection is declared as relatively strong, so reaching out may be a realistic support option."
        )

    if not notes:
        notes.append(
            "Your declared life context is being used as background information, not as a diagnosis."
        )

    return "Context note: " + " ".join(notes)


def _build_safety_first_message(
    tone: str,
    flag_types: list[str],
    life_event_note: str | None,
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

    message = (
        f"{opening} "
        f"Detected safety signal(s): {flags_text}. "
        "Miru is not a crisis service and this is not a diagnosis. "
        "If you feel at risk right now, contact local emergency services or reach out to someone you trust. "
        "For now, the safest next step is to pause, avoid staying alone with the situation if possible, "
        "and seek real human support."
    )

    if life_event_note is not None:
        message = f"{message} {life_event_note}"

    return message


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
    user_context_note: str,
    life_event_note: str | None,
) -> str:
    stress_label = _level_label(stress_level)
    energy_label = _level_label(energy_level)
    sleep_label = _level_label(sleep_quality)

    if tone == "direct":
        opening = "Direct reflection: Miru sees a few signals worth noticing."
    elif tone == "gentle":
        opening = "A gentle observation: there may be a few things worth noticing today."
    elif tone == "detailed":
        opening = (
            "Detailed reflection: Miru is combining your stable context, current state, "
            "recent insights, patterns, and available actions."
        )
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
        extra_state_notes.append(
            "Self-critical signals may be affecting your self-perception."
        )

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

    safety_sentence = "This is a reflection, not a diagnosis or medical advice."

    context_parts = [user_context_note]

    if life_event_note is not None:
        context_parts.append(life_event_note)

    parts = [
        opening,
        state_sentence,
        *context_parts,
        *extra_state_notes,
        insight_sentence,
        pattern_sentence,
        action_sentence,
        safety_sentence,
    ]

    return " ".join(parts)


def generate_reflection_response_for_user(
    db: Session,
    user_id: UUID,
) -> ReflectionResponse:
    reasoning_inputs = assemble_reasoning_inputs(
        db=db,
        user_id=user_id,
        insight_limit=3,
        pattern_limit=3,
        feedback_limit=10,
    )

    state = reasoning_inputs.current_state
    tone = _select_tone(reasoning_inputs)
    life_event_note = _build_life_event_note(
        reasoning_inputs.life_events,
    )

    if reasoning_inputs.open_safety_events:
        flag_types = sorted(
            {
                event.flag_type
                for event in reasoning_inputs.open_safety_events
            }
        )

        return create_reflection_response(
            db=db,
            user_id=user_id,
            source_type="manual",
            source_id=None,
            title="Safety check-in",
            message=_build_safety_first_message(
                tone=tone,
                flag_types=flag_types,
                life_event_note=life_event_note,
            ),
            tone=tone,
            response_type="gentle_checkin",
            suggested_action_id=None,
            source_snapshot_json={
                "safety_event_ids": [
                    str(event.id)
                    for event in reasoning_inputs.open_safety_events
                ],
                "safety_flag_types": flag_types,
                "life_event_ids": [
                    str(event.id)
                    for event in reasoning_inputs.life_events
                ],
                "life_events_available": len(reasoning_inputs.life_events) > 0,
                "user_context_available": reasoning_inputs.user_context is not None,
                "tone_source": tone,
                "coping_style_available": reasoning_inputs.coping_style is not None,
            },
        )

    latest_insights = reasoning_inputs.latest_insights
    latest_patterns = reasoning_inputs.latest_patterns
    top_action = _select_top_action(
    actions=reasoning_inputs.active_actions,
    coping_style=reasoning_inputs.coping_style,
)

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
        user_context_note=_build_user_context_note(reasoning_inputs.user_context),
        life_event_note=life_event_note,
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
        "life_event_ids": [
            str(event.id)
            for event in reasoning_inputs.life_events
        ],
        "life_events_available": len(reasoning_inputs.life_events) > 0,
        "user_context_available": reasoning_inputs.user_context is not None,
        "user_context_user_id": (
            str(reasoning_inputs.user_context.user_id)
            if reasoning_inputs.user_context
            else None
        ),
        "tone_source": tone,
        "coping_style_available": reasoning_inputs.coping_style is not None,
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
