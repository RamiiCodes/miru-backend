import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Float,
    Integer,
    String,
    Text,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ActionTemplate(Base):
    __tablename__ = "action_templates"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    code: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        unique=True,
        index=True,
    )

    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    action_type: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    # Flexible semantic matching metadata.
    match_semantic_tags_json: Mapped[list] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
        server_default=text("'[]'::jsonb"),
    )

    match_needs_json: Mapped[list] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
        server_default=text("'[]'::jsonb"),
    )

    match_life_domains_json: Mapped[list] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
        server_default=text("'[]'::jsonb"),
    )

    # Goal categories are data-driven template metadata.
    match_goal_categories_json: Mapped[list] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
        server_default=text("'[]'::jsonb"),
    )

    # Coping style matching is also configuration, not Python mapping.
    match_coping_styles_json: Mapped[list] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
        server_default=text("'[]'::jsonb"),
    )

    # Generic configurable conditions.
    #
    # Example:
    # {
    #   "source": "semantic",
    #   "dimension": "threat",
    #   "operator": "gte",
    #   "threshold": 0.6,
    #   "weight": 1.5
    # }
    #
    # Or:
    # {
    #   "source": "state",
    #   "dimension": "stress_level",
    #   "operator": "gte",
    #   "threshold": 0.7,
    #   "weight": 1.0
    # }
    conditions_json: Mapped[list] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
        server_default=text("'[]'::jsonb"),
    )

    base_priority: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=5,
        server_default="5",
    )

    base_confidence: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0.5,
        server_default="0.5",
    )

    minimum_score: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=1.0,
        server_default="1.0",
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
        index=True,
    )

    version: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
        server_default="1",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    __table_args__ = (
        CheckConstraint(
            "base_priority >= 1 AND base_priority <= 10",
            name="ck_action_templates_base_priority_range",
        ),
        CheckConstraint(
            "base_confidence >= 0 AND base_confidence <= 1",
            name="ck_action_templates_base_confidence_range",
        ),
        CheckConstraint(
            "minimum_score >= 0",
            name="ck_action_templates_minimum_score",
        ),
    )