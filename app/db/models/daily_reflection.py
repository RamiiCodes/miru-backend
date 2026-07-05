import uuid
from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class DailyReflection(Base):
    __tablename__ = "daily_reflections"

    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "reflection_date",
            name="uq_daily_reflection_user_date",
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

    reflection_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True,
    )

    title: Mapped[str] = mapped_column(String(255), nullable=False)

    summary: Mapped[str] = mapped_column(Text, nullable=False)

    emotional_state_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    insight_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    pattern_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    action_summary: Mapped[str | None] = mapped_column(Text, nullable=True)

    focus_areas: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)

    source_snapshot_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    model_version: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        default="daily_reflection_v0_1",
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