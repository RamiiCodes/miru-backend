from types import SimpleNamespace
from uuid import uuid4

from app.helpers.goal_action_ranker import (
    apply_goal_adjustments,
    get_goal_alignment_ids,
)


def _goal(
    category: str,
    priority: int = 5,
    status: str = "active",
):
    return SimpleNamespace(
        id=uuid4(),
        category=category,
        priority=priority,
        status=status,
    )


def test_primary_goal_match_boosts_priority_and_confidence():
    goal = _goal(
        category="stress_management",
        priority=5,
    )

    priority, confidence = apply_goal_adjustments(
        action_code="short_stress_pause",
        priority=5,
        confidence=0.60,
        user_goals=[goal],
    )

    assert priority == 7
    assert confidence == 0.72


def test_high_priority_goal_gets_extra_boost():
    goal = _goal(
        category="stress_management",
        priority=9,
    )

    priority, confidence = apply_goal_adjustments(
        action_code="short_stress_pause",
        priority=5,
        confidence=0.60,
        user_goals=[goal],
    )

    assert priority == 8
    assert confidence == 0.75


def test_secondary_goal_match_gets_smaller_boost():
    goal = _goal(
        category="stress_management",
        priority=5,
    )

    priority, confidence = apply_goal_adjustments(
        action_code="choose_one_small_next_step",
        priority=5,
        confidence=0.60,
        user_goals=[goal],
    )

    assert priority == 6
    assert confidence == 0.66


def test_paused_goal_does_not_adjust_action():
    goal = _goal(
        category="stress_management",
        priority=10,
        status="paused",
    )

    priority, confidence = apply_goal_adjustments(
        action_code="short_stress_pause",
        priority=5,
        confidence=0.60,
        user_goals=[goal],
    )

    assert priority == 5
    assert confidence == 0.60


def test_unrelated_goal_does_not_adjust_action():
    goal = _goal(
        category="sleep",
        priority=10,
    )

    priority, confidence = apply_goal_adjustments(
        action_code="self_criticism_reframe",
        priority=5,
        confidence=0.60,
        user_goals=[goal],
    )

    assert priority == 5
    assert confidence == 0.60


def test_goal_adjustments_are_capped():
    goals = [
        _goal(category="stress_management", priority=10),
        _goal(category="stress_management", priority=10),
        _goal(category="work_life_balance", priority=10),
    ]

    priority, confidence = apply_goal_adjustments(
        action_code="short_stress_pause",
        priority=8,
        confidence=0.85,
        user_goals=goals,
    )

    assert priority == 10
    assert confidence == 0.95


def test_get_goal_alignment_ids_returns_matching_active_goals_only():
    active_matching_goal = _goal(
        category="stress_management",
        priority=8,
    )

    paused_matching_goal = _goal(
        category="stress_management",
        priority=8,
        status="paused",
    )

    unrelated_goal = _goal(
    category="self_esteem",
    priority=8,
)

    goal_ids = get_goal_alignment_ids(
        action_code="short_stress_pause",
        user_goals=[
            active_matching_goal,
            paused_matching_goal,
            unrelated_goal,
        ],
    )

    assert goal_ids == [active_matching_goal.id]