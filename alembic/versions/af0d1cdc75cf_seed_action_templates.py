"""seed action templates

Revision ID: af0d1cdc75cf
Revises: 055f95d420fc
Create Date: 2026-07-14 15:05:35.625042

"""

import uuid
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql
from sqlalchemy.dialects.postgresql import insert as postgresql_insert


# revision identifiers, used by Alembic.
revision: str = "af0d1cdc75cf"
down_revision: Union[str, Sequence[str], None] = "055f95d420fc"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


ACTION_TEMPLATES = [
    {
        "code": "post_work_decompression_note",
        "title": "Create a short work decompression note",
        "content": (
            "Take a moment to write down what is still occupying your attention "
            "from work, then identify what can wait until later."
        ),
        "action_type": "reflection",
        "match_semantic_tags_json": [
            "work_pressure",
            "work_stress",
            "work_transition",
            "end_of_workday",
        ],
        "match_needs_json": [
            "decompression",
            "rest",
            "closure",
            "mental_space",
        ],
        "match_life_domains_json": [
            "career",
            "work",
        ],
        "match_goal_categories_json": [
            "work_life_balance",
            "stress_management",
            "emotional_awareness",
        ],
        "match_coping_styles_json": [],
        "conditions_json": [
            {
                "source": "semantic",
                "dimension": "threat",
                "operator": "gte",
                "threshold": 0.5,
                "weight": 0.75,
            },
            {
                "source": "state",
                "dimension": "stress_level",
                "operator": "gte",
                "threshold": 0.55,
                "weight": 1.0,
            },
        ],
        "base_priority": 5,
        "base_confidence": 0.55,
        "minimum_score": 1.0,
    },
    {
        "code": "name_the_looping_thought",
        "title": "Name the thought that keeps returning",
        "content": (
            "Write one sentence describing the thought that keeps returning. "
            "Focus on naming it rather than trying to solve it immediately."
        ),
        "action_type": "reflection",
        "match_semantic_tags_json": [
            "rumination",
            "repetitive_thought",
            "mental_loop",
            "overthinking",
        ],
        "match_needs_json": [
            "clarity",
            "distance",
            "grounding",
        ],
        "match_life_domains_json": [],
        "match_goal_categories_json": [
            "mental_clarity",
            "emotional_awareness",
            "stress_management",
        ],
        "match_coping_styles_json": [],
        "conditions_json": [
            {
                "source": "semantic",
                "dimension": "uncertainty",
                "operator": "gte",
                "threshold": 0.55,
                "weight": 0.75,
            },
        ],
        "base_priority": 5,
        "base_confidence": 0.55,
        "minimum_score": 1.0,
    },
    {
        "code": "balanced_self_response",
        "title": "Write a more balanced response to yourself",
        "content": (
            "Write what you are currently telling yourself, then write a second "
            "response that is fair, specific, and less absolute."
        ),
        "action_type": "reflection",
        "match_semantic_tags_json": [
            "self_criticism",
            "harsh_self_evaluation",
            "shame",
            "negative_self_judgment",
        ],
        "match_needs_json": [
            "self_compassion",
            "perspective",
            "emotional_balance",
        ],
        "match_life_domains_json": [
            "identity",
            "personal_growth",
        ],
        "match_goal_categories_json": [
            "self_esteem",
            "emotional_awareness",
            "personal_growth",
        ],
        "match_coping_styles_json": [],
        "conditions_json": [
            {
                "source": "semantic",
                "dimension": "self_evaluation",
                "operator": "lte",
                "threshold": 0.4,
                "weight": 1.5,
            },
        ],
        "base_priority": 5,
        "base_confidence": 0.55,
        "minimum_score": 1.0,
    },
    {
        "code": "sleep_stress_wind_down",
        "title": "Create a short wind-down boundary",
        "content": (
            "Choose one small activity that marks the end of the day, and pause "
            "work, planning, or problem-solving until tomorrow."
        ),
        "action_type": "routine",
        "match_semantic_tags_json": [
            "sleep_disruption",
            "bedtime_stress",
            "mental_activation",
            "difficulty_winding_down",
        ],
        "match_needs_json": [
            "rest",
            "decompression",
            "sleep",
            "calm",
        ],
        "match_life_domains_json": [
            "health",
            "daily_routine",
        ],
        "match_goal_categories_json": [
            "sleep",
            "stress_management",
            "habit_building",
        ],
        "match_coping_styles_json": [],
        "conditions_json": [
            {
                "source": "state",
                "dimension": "sleep_quality",
                "operator": "lte",
                "threshold": 0.45,
                "weight": 1.5,
            },
            {
                "source": "state",
                "dimension": "stress_level",
                "operator": "gte",
                "threshold": 0.6,
                "weight": 0.75,
            },
        ],
        "base_priority": 6,
        "base_confidence": 0.55,
        "minimum_score": 1.0,
    },
    {
        "code": "two_column_thought_check",
        "title": "Separate facts from interpretations",
        "content": (
            "Create two short columns: what you know directly, and what you are "
            "currently assuming or predicting."
        ),
        "action_type": "reflection",
        "match_semantic_tags_json": [
            "uncertainty",
            "worry",
            "rumination",
            "conflicting_interpretations",
        ],
        "match_needs_json": [
            "clarity",
            "perspective",
            "reality_check",
        ],
        "match_life_domains_json": [],
        "match_goal_categories_json": [
            "mental_clarity",
            "emotional_awareness",
            "personal_growth",
        ],
        "match_coping_styles_json": [],
        "conditions_json": [
            {
                "source": "semantic",
                "dimension": "uncertainty",
                "operator": "gte",
                "threshold": 0.55,
                "weight": 1.25,
            },
        ],
        "base_priority": 5,
        "base_confidence": 0.55,
        "minimum_score": 1.0,
    },
    {
        "code": "self_criticism_reframe",
        "title": "Reframe one self-critical statement",
        "content": (
            "Choose one self-critical statement and rewrite it using specific "
            "facts, temporary language, and the same fairness you would offer someone else."
        ),
        "action_type": "reflection",
        "match_semantic_tags_json": [
            "self_criticism",
            "failure_narrative",
            "perfectionism",
            "harsh_self_evaluation",
        ],
        "match_needs_json": [
            "self_compassion",
            "perspective",
            "acceptance",
        ],
        "match_life_domains_json": [
            "identity",
            "personal_growth",
        ],
        "match_goal_categories_json": [
            "self_esteem",
            "personal_growth",
            "emotional_awareness",
        ],
        "match_coping_styles_json": [],
        "conditions_json": [
            {
                "source": "semantic",
                "dimension": "self_evaluation",
                "operator": "lte",
                "threshold": 0.35,
                "weight": 1.5,
            },
        ],
        "base_priority": 6,
        "base_confidence": 0.55,
        "minimum_score": 1.0,
    },
    {
        "code": "choose_one_small_next_step",
        "title": "Choose one small next step",
        "content": (
            "Identify one action that is small enough to complete without solving "
            "the entire situation."
        ),
        "action_type": "planning",
        "match_semantic_tags_json": [
            "stuck",
            "indecision",
            "low_control",
            "overwhelm",
            "low_momentum",
        ],
        "match_needs_json": [
            "agency",
            "clarity",
            "momentum",
            "direction",
        ],
        "match_life_domains_json": [],
        "match_goal_categories_json": [
            "habit_building",
            "personal_growth",
            "mental_clarity",
            "grief_processing",
        ],
        "match_coping_styles_json": [],
        "conditions_json": [
            {
                "source": "semantic",
                "dimension": "control",
                "operator": "lte",
                "threshold": 0.4,
                "weight": 1.5,
            },
            {
                "source": "state",
                "dimension": "motivation",
                "operator": "lte",
                "threshold": 0.45,
                "weight": 0.75,
            },
        ],
        "base_priority": 6,
        "base_confidence": 0.55,
        "minimum_score": 1.0,
    },
    {
        "code": "work_trigger_note",
        "title": "Record the specific work trigger",
        "content": (
            "Write down the specific work moment that changed your state, what "
            "happened immediately before it, and what you noticed afterward."
        ),
        "action_type": "reflection",
        "match_semantic_tags_json": [
            "work_trigger",
            "work_pressure",
            "work_conflict",
            "performance_pressure",
        ],
        "match_needs_json": [
            "clarity",
            "awareness",
            "pattern_recognition",
        ],
        "match_life_domains_json": [
            "career",
            "work",
        ],
        "match_goal_categories_json": [
            "work_life_balance",
            "emotional_awareness",
            "stress_management",
        ],
        "match_coping_styles_json": [],
        "conditions_json": [
            {
                "source": "semantic",
                "dimension": "threat",
                "operator": "gte",
                "threshold": 0.5,
                "weight": 0.75,
            },
        ],
        "base_priority": 5,
        "base_confidence": 0.55,
        "minimum_score": 1.0,
    },
    {
        "code": "short_stress_pause",
        "title": "Take a short pause",
        "content": (
            "Pause briefly, reduce incoming stimulation, and bring your attention "
            "to one immediate physical sensation or steady point around you."
        ),
        "action_type": "regulation",
        "match_semantic_tags_json": [
            "high_pressure",
            "overwhelm",
            "acute_stress",
            "high_activation",
        ],
        "match_needs_json": [
            "grounding",
            "rest",
            "regulation",
            "calm",
        ],
        "match_life_domains_json": [],
        "match_goal_categories_json": [
            "stress_management",
        ],
        "match_coping_styles_json": [],
        "conditions_json": [
            {
                "source": "semantic",
                "dimension": "threat",
                "operator": "gte",
                "threshold": 0.6,
                "weight": 1.5,
            },
            {
                "source": "state",
                "dimension": "stress_level",
                "operator": "gte",
                "threshold": 0.6,
                "weight": 1.5,
            },
        ],
        "base_priority": 7,
        "base_confidence": 0.6,
        "minimum_score": 1.0,
    },
    {
        "code": "reduce_scope_today",
        "title": "Reduce today's scope",
        "content": (
            "Choose what truly needs attention today and explicitly postpone one "
            "or more lower-priority demands."
        ),
        "action_type": "planning",
        "match_semantic_tags_json": [
            "overwhelm",
            "overload",
            "too_many_demands",
            "low_control",
        ],
        "match_needs_json": [
            "simplification",
            "agency",
            "rest",
            "prioritization",
        ],
        "match_life_domains_json": [
            "career",
            "work",
            "daily_routine",
        ],
        "match_goal_categories_json": [
            "stress_management",
            "work_life_balance",
            "habit_building",
        ],
        "match_coping_styles_json": [],
        "conditions_json": [
            {
                "source": "semantic",
                "dimension": "control",
                "operator": "lte",
                "threshold": 0.35,
                "weight": 1.25,
            },
            {
                "source": "state",
                "dimension": "stress_level",
                "operator": "gte",
                "threshold": 0.7,
                "weight": 1.5,
            },
        ],
        "base_priority": 7,
        "base_confidence": 0.6,
        "minimum_score": 1.0,
    },
    {
        "code": "low_pressure_connection",
        "title": "Make a low-pressure connection",
        "content": (
            "Consider a small, manageable form of contact with someone you trust, "
            "without requiring a long or difficult conversation."
        ),
        "action_type": "social",
        "match_semantic_tags_json": [
            "isolation",
            "social_withdrawal",
            "disconnection",
            "loneliness",
        ],
        "match_needs_json": [
            "connection",
            "support",
            "companionship",
        ],
        "match_life_domains_json": [
            "relationship",
            "family",
            "social",
        ],
        "match_goal_categories_json": [
            "social_connection",
            "grief_processing",
        ],
        "match_coping_styles_json": [],
        "conditions_json": [
            {
                "source": "semantic",
                "dimension": "social_connection",
                "operator": "lte",
                "threshold": 0.4,
                "weight": 1.5,
            },
            {
                "source": "state",
                "dimension": "social_connection",
                "operator": "lte",
                "threshold": 0.4,
                "weight": 1.5,
            },
        ],
        "base_priority": 6,
        "base_confidence": 0.55,
        "minimum_score": 1.0,
    },
]


ACTION_TEMPLATE_CODES = [
    template["code"]
    for template in ACTION_TEMPLATES
]


def _action_templates_table() -> sa.TableClause:
    return sa.table(
        "action_templates",
        sa.column(
            "id",
            postgresql.UUID(as_uuid=True),
        ),
        sa.column(
            "code",
            sa.String(length=100),
        ),
        sa.column(
            "title",
            sa.String(length=255),
        ),
        sa.column(
            "content",
            sa.Text(),
        ),
        sa.column(
            "action_type",
            sa.String(length=100),
        ),
        sa.column(
            "match_semantic_tags_json",
            postgresql.JSONB(),
        ),
        sa.column(
            "match_needs_json",
            postgresql.JSONB(),
        ),
        sa.column(
            "match_life_domains_json",
            postgresql.JSONB(),
        ),
        sa.column(
            "match_goal_categories_json",
            postgresql.JSONB(),
        ),
        sa.column(
            "match_coping_styles_json",
            postgresql.JSONB(),
        ),
        sa.column(
            "conditions_json",
            postgresql.JSONB(),
        ),
        sa.column(
            "base_priority",
            sa.Integer(),
        ),
        sa.column(
            "base_confidence",
            sa.Float(),
        ),
        sa.column(
            "minimum_score",
            sa.Float(),
        ),
        sa.column(
            "is_active",
            sa.Boolean(),
        ),
        sa.column(
            "version",
            sa.Integer(),
        ),
    )


def upgrade() -> None:
    """Seed configurable action templates."""

    connection = op.get_bind()
    action_templates = _action_templates_table()

    for template in ACTION_TEMPLATES:
        statement = postgresql_insert(
            action_templates
        ).values(
            id=uuid.uuid4(),
            **template,
            is_active=True,
            version=1,
        )

        statement = statement.on_conflict_do_nothing(
            index_elements=["code"],
        )

        connection.execute(statement)


def downgrade() -> None:
    """Remove the action templates introduced by this migration."""

    connection = op.get_bind()
    action_templates = _action_templates_table()

    connection.execute(
        action_templates.delete().where(
            action_templates.c.code.in_(
                ACTION_TEMPLATE_CODES
            )
        )
    )