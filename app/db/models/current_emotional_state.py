import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, Float, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class CurrentEmotionalState(Base):
    __tablename__ = "current_emotional_states"

    __table_args__ = (
        CheckConstraint("stress_level IS NULL OR (stress_level >= 0 AND stress_level <= 1)", name="ck_state_stress_range"),
        CheckConstraint("energy_level IS NULL OR (energy_level >= 0 AND energy_level <= 1)", name="ck_state_energy_range"),
        CheckConstraint("sleep_quality IS NULL OR (sleep_quality >= 0 AND sleep_quality <= 1)", name="ck_state_sleep_range"),
        CheckConstraint("social_connection IS NULL OR (social_connection >= 0 AND social_connection <= 1)", name="ck_state_social_range"),
        CheckConstraint("emotional_stability IS NULL OR (emotional_stability >= 0 AND emotional_stability <= 1)", name="ck_state_emotional_stability_range"),
        CheckConstraint("motivation IS NULL OR (motivation >= 0 AND motivation <= 1)", name="ck_state_motivation_range"),
        CheckConstraint("self_esteem IS NULL OR (self_esteem >= 0 AND self_esteem <= 1)", name="ck_state_self_esteem_range"),
        CheckConstraint("physical_activity IS NULL OR (physical_activity >= 0 AND physical_activity <= 1)", name="ck_state_physical_activity_range"),
        CheckConstraint("eating_habits IS NULL OR (eating_habits >= 0 AND eating_habits <= 1)", name="ck_state_eating_habits_range"),
        CheckConstraint("confidence >= 0 AND confidence <= 1", name="ck_state_confidence_range"),
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

    stress_level: Mapped[float | None] = mapped_column(Float, nullable=True)
    energy_level: Mapped[float | None] = mapped_column(Float, nullable=True)
    sleep_quality: Mapped[float | None] = mapped_column(Float, nullable=True)
    social_connection: Mapped[float | None] = mapped_column(Float, nullable=True)
    emotional_stability: Mapped[float | None] = mapped_column(Float, nullable=True)

    motivation: Mapped[float | None] = mapped_column(Float, nullable=True)
    self_esteem: Mapped[float | None] = mapped_column(Float, nullable=True)
    physical_activity: Mapped[float | None] = mapped_column(Float, nullable=True)
    eating_habits: Mapped[float | None] = mapped_column(Float, nullable=True)

    confidence: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0.0,
    )

    model_version: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        default="current_emotional_state_v0_1",
    )

    calculated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )