import uuid
from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class JournalSemanticFrame(Base):
    __tablename__ = "journal_semantic_frames"

    __table_args__ = (
        CheckConstraint(
            "overall_confidence IS NULL OR "
            "(overall_confidence >= 0 AND overall_confidence <= 1)",
            name="ck_journal_semantic_frames_overall_confidence_range",
        ),
        UniqueConstraint(
            "journal_analysis_id",
            name="uq_journal_semantic_frames_journal_analysis_id",
        ),
        Index("ix_journal_semantic_frames_user_created", "user_id", "created_at"),
        Index(
            "ix_journal_semantic_frames_semantic_tags_gin",
            "semantic_tags_json",
            postgresql_using="gin",
        ),
        Index(
            "ix_journal_semantic_frames_life_domains_gin",
            "life_domains_json",
            postgresql_using="gin",
        ),
        Index(
            "ix_journal_semantic_frames_needs_gin",
            "needs_json",
            postgresql_using="gin",
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

    provider: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )

    model_name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    prompt_version: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    core_dimensions_json: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
    )

    emotion_labels_json: Mapped[list] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
    )

    semantic_tags_json: Mapped[list] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
    )

    life_domains_json: Mapped[list] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
    )

    needs_json: Mapped[list] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
    )

    additional_dimensions_json: Mapped[list] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
    )

    event_candidates_json: Mapped[list] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
    )

    safety_flags_json: Mapped[list] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
    )

    overall_confidence: Mapped[float | None] = mapped_column(
        nullable=True,
    )

    raw_output_json: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )