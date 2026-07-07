import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class SafetyEvent(Base):
    __tablename__ = "safety_events"

    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "source_type",
            "source_id",
            "flag_type",
            name="uq_safety_event_user_source_flag",
        ),
        CheckConstraint(
            "flag_type IN ('self_harm_risk', 'harm_to_others_risk', 'abuse_or_coercion_context', 'severe_distress')",
            name="ck_safety_event_flag_type",
        ),
        CheckConstraint(
            "severity IN ('low', 'medium', 'high', 'critical')",
            name="ck_safety_event_severity",
        ),
        CheckConstraint(
            "status IN ('open', 'acknowledged', 'resolved')",
            name="ck_safety_event_status",
        ),
        CheckConstraint(
            "source_type IN ('journal_entry', 'reflection_response', 'manual')",
            name="ck_safety_event_source_type",
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

    flag_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)

    severity: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="medium",
        index=True,
    )

    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="open",
        index=True,
    )

    source_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)

    source_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        index=True,
    )

    message: Mapped[str] = mapped_column(Text, nullable=False)

    acknowledged_at: Mapped[datetime | None] = mapped_column(
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