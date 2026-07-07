from dataclasses import dataclass
from uuid import UUID

from sqlalchemy.orm import Session

from app.db.models.action_suggestion import ActionSuggestion
from app.db.models.basic_insight import BasicInsight
from app.db.models.current_emotional_state import CurrentEmotionalState
from app.db.models.pattern_detection import PatternDetection
from app.db.models.safety_event import SafetyEvent
from app.db.models.user_context import UserContext
from app.db.models.user_feedback import UserFeedback
from app.db.models.user_profile import UserProfile
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
from app.db.repositories.safety_event_repository import list_open_safety_events_by_user_id
from app.db.repositories.user_context_repository import get_user_context_by_user_id
from app.db.repositories.user_feedback_repository import list_user_feedback_by_user_id
from app.db.repositories.user_profile_repository import get_user_profile_by_user_id


"""
Technical helper.

This is not the Signal Processing System from the Miru cognitive architecture.

Signal Processing System:
    Raw inputs -> normalized UserSignals

ReasoningInputAssembler:
    Already-computed reasoning data -> one snapshot for downstream systems

Used by:
    - Reflection System
    - Daily Reflection System
    - future LLM prompt builders
    - future Recommendation reasoning
"""


@dataclass(frozen=True)
class ReasoningInputs:
    profile: UserProfile | None
    user_context: UserContext | None
    current_state: CurrentEmotionalState | None
    latest_insights: list[BasicInsight]
    latest_patterns: list[PatternDetection]
    active_actions: list[ActionSuggestion]
    latest_feedback: list[UserFeedback]
    open_safety_events: list[SafetyEvent]


def assemble_reasoning_inputs(
    db: Session,
    user_id: UUID,
    insight_limit: int = 5,
    pattern_limit: int = 5,
    feedback_limit: int = 10,
) -> ReasoningInputs:
    insights = list_basic_insights_by_user_id(
        db=db,
        user_id=user_id,
    )

    patterns = list_pattern_detections_by_user_id(
        db=db,
        user_id=user_id,
    )

    feedback = list_user_feedback_by_user_id(
        db=db,
        user_id=user_id,
    )

    active_actions = list_action_suggestions_by_user_id(
        db=db,
        user_id=user_id,
        include_completed=False,
        include_dismissed=False,
    )

    return ReasoningInputs(
        profile=get_user_profile_by_user_id(
            db=db,
            user_id=user_id,
        ),
        user_context=get_user_context_by_user_id(
            db=db,
            user_id=user_id,
        ),
        current_state=get_latest_current_emotional_state(
            db=db,
            user_id=user_id,
        ),
        latest_insights=insights[:insight_limit],
        latest_patterns=patterns[:pattern_limit],
        active_actions=active_actions,
        latest_feedback=feedback[:feedback_limit],
        open_safety_events=list_open_safety_events_by_user_id(
            db=db,
            user_id=user_id,
        ),
    )