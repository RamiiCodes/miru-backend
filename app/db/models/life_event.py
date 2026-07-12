import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class LifeEvent(Base):
    __tablename__ = "life_events"

    __table_args__ = (
        CheckConstraint(
            "category IN ("
            "'family', "
            "'relationship', "
            "'career', "
            "'education', "
            "'health', "
            "'financial', "
            "'relocation', "
            "'legal', "
            "'trauma', "
            "'achievement', "
            "'personal_growth', "
            "'other'"
            ")",
            name="ck_life_events_category",
        ),
        CheckConstraint(
            "confirmation_status IN ("
            "'candidate', "
            "'confirmed', "
            "'partially_confirmed', "
            "'dismissed'"
            ")",
            name="ck_life_events_confirmation_status",
        ),
        CheckConstraint(
            "source_type IN ("
            "'manual', "
            "'journal_analysis', "
            "'user_registration', "
            "'user_narrative'"
            ")",
            name="ck_life_events_source_type",
        ),
        CheckConstraint(
            "event_date_precision IN ("
            "'unknown', "
            "'year', "
            "'month', "
            "'day', "
            "'exact'"
            ")",
            name="ck_life_events_event_date_precision",
        ),
        CheckConstraint(
            "emotional_impact IS NULL OR "
            "(emotional_impact >= 1 AND emotional_impact <= 10)",
            name="ck_life_events_emotional_impact_range",
        ),
        CheckConstraint(
            "confidence IS NULL OR "
            "(confidence >= 0 AND confidence <= 1)",
            name="ck_life_events_confidence_range",
        ),
        UniqueConstraint(
            "user_id",
            "source_type",
            "source_id",
            "event_type",
            name="uq_life_events_source_event_type",
        ),
        Index("ix_life_events_user_event_date", "user_id", "event_date"),
        Index("ix_life_events_user_category", "user_id", "category"),
        Index("ix_life_events_user_confirmation_status", "user_id", "confirmation_status"),
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

    event_type: Mapped[str] = mapped_column(
        String(100),
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

    emotional_impact: Mapped[int | None] = mapped_column(
        SmallInteger,
        nullable=True,
        index=True,
    )

    event_date: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
    )

    event_date_precision: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="unknown",
    )

    confirmation_status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="candidate",
        index=True,
    )

    confidence: Mapped[float | None] = mapped_column(
        nullable=True,
    )

    evidence: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )

    version: Mapped[int] = mapped_column(
        nullable=False,
        default=1,
    )

    supersedes_event_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("life_events.id", ondelete="SET NULL"),
        nullable=True,
    )

    detected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
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