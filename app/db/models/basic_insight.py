import uuid
from datetime import datetime
from sqlalchemy import CheckConstraint, DateTime, Float, ForeignKey, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class BasicInsight(Base):
    __tablename__ = "basic_insights"

    __table_args__ = (
        UniqueConstraint("state_id", "rule_code", name="uq_basic_insight_state_rule"),
        CheckConstraint("confidence >= 0 AND confidence <= 1", name="ck_basic_insight_confidence_range"),
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

    state_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("current_emotional_states.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    rule_code: Mapped[str] = mapped_column(String(100), nullable=False, index=True)

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)

    insight_type: Mapped[str] = mapped_column(String(100), nullable=False)
    severity: Mapped[str] = mapped_column(String(50), nullable=False)

    confidence: Mapped[float] = mapped_column(Float, nullable=False)

    model_version: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        default="basic_insight_v0_1",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )