import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class JournalAnalysis(Base):
    __tablename__ = "journal_analyses"

    __table_args__ = (
        UniqueConstraint(
            "journal_entry_id",
            name="uq_journal_analyses_journal_entry_id",
        ),
        CheckConstraint(
            "status IN ('success', 'failed')",
            name="ck_journal_analyses_status",
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

    provider: Mapped[str] = mapped_column(String(100), nullable=False)
    model_name: Mapped[str] = mapped_column(String(150), nullable=False)
    prompt_version: Mapped[str] = mapped_column(String(100), nullable=False)

    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="success",
        index=True,
    )

    language: Mapped[str | None] = mapped_column(String(20), nullable=True)

    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    emotional_tone: Mapped[str | None] = mapped_column(String(150), nullable=True)

    safety_flags: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)
    themes: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)

    life_event_candidates_json: Mapped[list[dict] | None] = mapped_column(
        JSONB,
        nullable=True,
    )

    raw_output_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    latency_ms: Mapped[int | None] = mapped_column(nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )