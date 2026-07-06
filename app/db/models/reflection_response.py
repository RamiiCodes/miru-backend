import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ReflectionResponse(Base):
    __tablename__ = "reflection_responses"

    __table_args__ = (
        CheckConstraint(
            "tone IN ('balanced', 'direct', 'gentle', 'detailed')",
            name="ck_reflection_response_tone",
        ),
        CheckConstraint(
            "response_type IN ('supportive_reflection', 'action_oriented', 'summary', 'gentle_checkin')",
            name="ck_reflection_response_type",
        ),
        CheckConstraint(
            "source_type IN ('current_emotional_state', 'daily_reflection', 'journal_entry', 'manual')",
            name="ck_reflection_response_source_type",
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

    source_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)

    source_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        index=True,
    )

    title: Mapped[str] = mapped_column(String(255), nullable=False)

    message: Mapped[str] = mapped_column(Text, nullable=False)

    tone: Mapped[str] = mapped_column(String(50), nullable=False, default="balanced")

    response_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        default="supportive_reflection",
        index=True,
    )

    suggested_action_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        index=True,
    )

    source_snapshot_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    model_version: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        default="reflection_response_v0_1",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )