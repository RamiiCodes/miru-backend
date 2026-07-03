import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class StructuredCheckin(Base):
    __tablename__ = "structured_checkins"

    __table_args__ = (
        CheckConstraint("mood_score >= 0 AND mood_score <= 10", name="ck_mood_score_range"),
        CheckConstraint("stress_score >= 0 AND stress_score <= 10", name="ck_stress_score_range"),
        CheckConstraint("energy_score >= 0 AND energy_score <= 10", name="ck_energy_score_range"),
        CheckConstraint("sleep_score >= 0 AND sleep_score <= 10", name="ck_sleep_score_range"),
        CheckConstraint("social_score >= 0 AND social_score <= 10", name="ck_social_score_range"),
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

    mood_score: Mapped[int] = mapped_column(Integer, nullable=False)
    stress_score: Mapped[int] = mapped_column(Integer, nullable=False)
    energy_score: Mapped[int] = mapped_column(Integer, nullable=False)
    sleep_score: Mapped[int] = mapped_column(Integer, nullable=False)
    social_score: Mapped[int] = mapped_column(Integer, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )

    user = relationship(
        "User",
        back_populates="structured_checkins",
    )