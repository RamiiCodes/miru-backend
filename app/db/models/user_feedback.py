import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class UserFeedback(Base):
    __tablename__ = "user_feedback"

    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "target_type",
            "target_id",
            name="uq_user_feedback_user_target",
        ),
        CheckConstraint(
            "rating IN ('useful', 'not_useful', 'inaccurate', 'too_direct', 'too_vague', 'not_relevant')",
            name="ck_user_feedback_rating",
        ),
        CheckConstraint(
            "target_type IN ('basic_insight', 'action_suggestion', 'daily_reflection', 'pattern_detection', 'reflection_response')",
            name="ck_user_feedback_target_type",
        ),
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

    target_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )

    target_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        index=True,
    )

    rating: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )

    comment: Mapped[str | None] = mapped_column(
        Text,
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