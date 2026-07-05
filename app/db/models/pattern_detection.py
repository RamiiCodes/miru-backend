import uuid
from datetime import date, datetime

from sqlalchemy import CheckConstraint, Date, DateTime, Float, ForeignKey, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class PatternDetection(Base):
    __tablename__ = "pattern_detections"

    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "pattern_code",
            "window_start_date",
            "window_end_date",
            name="uq_pattern_detection_user_code_window",
        ),
        CheckConstraint("confidence >= 0 AND confidence <= 1", name="ck_pattern_detection_confidence_range"),
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

    pattern_code: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
        index=True,
    )

    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    pattern_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )

    severity: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )

    confidence: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    evidence_json: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
    )

    window_start_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True,
    )

    window_end_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True,
    )

    detection_window_days: Mapped[int] = mapped_column(
        nullable=False,
        default=14,
    )

    model_version: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        default="pattern_detection_v0_1",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )