import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class JournalExtractedSignal(Base):
    __tablename__ = "journal_extracted_signals"

    __table_args__ = (
        UniqueConstraint(
            "journal_analysis_id",
            "signal_code",
            name="uq_journal_extracted_signals_analysis_signal",
        ),
        CheckConstraint(
            "value >= 0 AND value <= 1",
            name="ck_journal_extracted_signals_value_range",
        ),
        CheckConstraint(
            "confidence >= 0 AND confidence <= 1",
            name="ck_journal_extracted_signals_confidence_range",
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

    journal_entry_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("journal_entries.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    journal_analysis_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("journal_analyses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    signal_code: Mapped[str] = mapped_column(String(100), nullable=False, index=True)

    value: Mapped[float] = mapped_column(nullable=False)
    confidence: Mapped[float] = mapped_column(nullable=False)

    evidence: Mapped[str | None] = mapped_column(Text, nullable=True)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )