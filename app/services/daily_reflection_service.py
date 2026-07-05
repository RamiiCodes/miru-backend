from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.orm import Session

from app.db.models.daily_reflection import DailyReflection
from app.db.repositories.action_suggestion_repository import (
    list_action_suggestions_by_user_id,
)
from app.db.repositories.basic_insight_repository import list_basic_insights_by_user_id
from app.db.repositories.current_emotional_state_repository import (
    get_latest_current_emotional_state,
)
from app.db.repositories.daily_reflection_repository import upsert_daily_reflection
from app.db.repositories.pattern_detection_repository import (
    list_pattern_detections_by_user_id,
)


PRIORITY_ORDER = {
    "high": 3,
    "medium": 2,
    "low": 1,
}


def _state_level_label(value: float | None) -> str:
    if value is None:
        return "unknown"

    if value >= 0.75:
        return "elevated"

    if value >= 0.45:
        return "moderate"

    return "lower"


def _build_focus_areas(
    insight_codes: set[str],
    pattern_codes: set[str],
    state_stress_level: float | None,
) -> list[str]:
    focus_areas: set[str] = set()

    if state_stress_level is not None and state_stress_level >= 0.7:
        focus_areas.add("stress")

    if "work_context_stress_connection" in insight_codes:
        focus_areas.add("work_context")

    if "stress_rumination_connection" in insight_codes:
        focus_areas.add("rumination")

    if "self_criticism_self_esteem_connection" in insight_codes:
        focus_areas.add("self_criticism")

    if "fear_failure_motivation_connection" in insight_codes:
        focus_areas.add("motivation")

    if "repeated_work_stress" in pattern_codes:
        focus_areas.add("repeated_work_stress")

    if "repeated_rumination" in pattern_codes:
        focus_areas.add("repeated_rumination")

    if "repeated_self_criticism" in pattern_codes:
        focus_areas.add("repeated_self_criticism")

    return sorted(focus_areas)


def generate_daily_reflection_for_user(
    db: Session,
    user_id: UUID,
) -> DailyReflection:
    today = datetime.now(timezone.utc).date()

    state = get_latest_current_emotional_state(db=db, user_id=user_id)
    insights = list_basic_insights_by_user_id(db=db, user_id=user_id)
    patterns = list_pattern_detections_by_user_id(db=db, user_id=user_id)
    actions = list_action_suggestions_by_user_id(
        db=db,
        user_id=user_id,
        include_completed=False,
        include_dismissed=False,
    )

    latest_insights = insights[:5]
    latest_patterns = patterns[:5]

    sorted_actions = sorted(
        actions,
        key=lambda action: PRIORITY_ORDER.get(action.priority, 0),
        reverse=True,
    )

    top_actions = sorted_actions[:3]

    if state is None:
        emotional_state_summary = (
            "Miru does not have enough current state data yet. A check-in can help "
            "build today’s reflection."
        )
    else:
        stress_label = _state_level_label(state.stress_level)
        energy_label = _state_level_label(state.energy_level)
        sleep_label = _state_level_label(state.sleep_quality)

        emotional_state_summary = (
            f"Your current stress level appears {stress_label}. "
            f"Energy appears {energy_label}, and sleep quality appears {sleep_label}."
        )

        if state.motivation is not None and state.motivation <= 0.4:
            emotional_state_summary += (
                " Motivation may currently be lower than usual."
            )

        if state.self_esteem is not None and state.self_esteem <= 0.4:
            emotional_state_summary += (
                " Self-critical signals may also be affecting your self-perception."
            )

    if latest_insights:
        insight_titles = [insight.title for insight in latest_insights[:3]]
        insight_summary = "Recent insights suggest: " + "; ".join(insight_titles) + "."
    else:
        insight_summary = "No specific insight has been generated yet."

    if latest_patterns:
        pattern_titles = [pattern.title for pattern in latest_patterns[:3]]
        pattern_summary = "Recent patterns detected: " + "; ".join(pattern_titles) + "."
    else:
        pattern_summary = "No repeated multi-day pattern has been detected yet."

    if top_actions:
        action_titles = [action.title for action in top_actions]
        action_summary = (
            "A possible next step today: "
            + action_titles[0]
            + "."
        )

        if len(action_titles) > 1:
            action_summary += (
                " Other options include: "
                + "; ".join(action_titles[1:])
                + "."
            )
    else:
        action_summary = (
            "No action suggestion is currently available. A check-in or journal entry "
            "can help Miru suggest a small next step."
        )

    insight_codes = {insight.rule_code for insight in latest_insights}
    pattern_codes = {pattern.pattern_code for pattern in latest_patterns}

    focus_areas = _build_focus_areas(
        insight_codes=insight_codes,
        pattern_codes=pattern_codes,
        state_stress_level=state.stress_level if state else None,
    )

    if focus_areas:
        title = "Today’s reflection: " + ", ".join(focus_areas[:2]).replace("_", " ")
    else:
        title = "Today’s reflection"

    summary = (
        f"{emotional_state_summary} "
        f"{insight_summary} "
        f"{pattern_summary} "
        f"{action_summary}"
    )

    source_snapshot_json = {
        "state_id": str(state.id) if state else None,
        "insight_ids": [str(insight.id) for insight in latest_insights],
        "pattern_ids": [str(pattern.id) for pattern in latest_patterns],
        "action_ids": [str(action.id) for action in top_actions],
    }

    return upsert_daily_reflection(
        db=db,
        user_id=user_id,
        reflection_date=today,
        title=title,
        summary=summary,
        emotional_state_summary=emotional_state_summary,
        insight_summary=insight_summary,
        pattern_summary=pattern_summary,
        action_summary=action_summary,
        focus_areas=focus_areas,
        source_snapshot_json=source_snapshot_json,
    )
