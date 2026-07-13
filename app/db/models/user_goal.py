import uuid
from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class UserGoal(Base):
    __tablename__ = "user_goals"

    __table_args__ = (
        CheckConstraint(
            "category IN ("
            "'stress_management', "
            "'sleep', "
            "'emotional_awareness', "
            "'self_esteem', "
            "'social_connection', "
            "'work_life_balance', "
            "'grief_processing', "
            "'habit_building', "
            "'personal_growth', "
            "'mental_clarity', "
            "'other'"
            ")",
            name="ck_user_goals_category",
        ),
        CheckConstraint(
            "time_horizon IN ("
            "'short_term', "
            "'medium_term', "
            "'long_term', "
            "'ongoing'"
            ")",
            name="ck_user_goals_time_horizon",
        ),
        CheckConstraint(
            "status IN ("
            "'active', "
            "'paused', "
            "'completed', "
            "'archived'"
            ")",
            name="ck_user_goals_status",
        ),
        CheckConstraint(
            "source_type IN ("
            "'manual', "
            "'onboarding', "
            "'reflection_response', "
            "'life_event', "
            "'journal_analysis'"
            ")",
            name="ck_user_goals_source_type",
        ),
        CheckConstraint(
            "priority >= 1 AND priority <= 10",
            name="ck_user_goals_priority_range",
        ),
        CheckConstraint(
            "progress >= 0 AND progress <= 1",
            name="ck_user_goals_progress_range",
        ),
        CheckConstraint(
            "confidence IS NULL OR (confidence >= 0 AND confidence <= 1)",
            name="ck_user_goals_confidence_range",
        ),
        Index("ix_user_goals_user_status", "user_id", "status"),
        Index("ix_user_goals_user_category", "user_id", "category"),
        Index("ix_user_goals_user_priority", "user_id", "priority"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    source_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="manual",
        index=True,
    )

    source_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        index=True,
    )

    category: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )

    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    priority: Mapped[int] = mapped_column(
        nullable=False,
        default=5,
        index=True,
    )

    time_horizon: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="ongoing",
        index=True,
    )

    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="active",
        index=True,
    )

    progress: Mapped[float] = mapped_column(
        nullable=False,
        default=0.0,
    )

    confidence: Mapped[float | None] = mapped_column(
        nullable=True,
    )

    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )