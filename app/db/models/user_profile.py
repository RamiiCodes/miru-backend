import uuid
from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class UserProfile(Base):
    __tablename__ = "user_profiles"

    __table_args__ = (
        UniqueConstraint("user_id", name="uq_user_profiles_user_id"),
        CheckConstraint(
            "preferred_reflection_style IN ('balanced', 'direct', 'gentle', 'detailed')",
            name="ck_user_profile_reflection_style",
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

    display_name: Mapped[str | None] = mapped_column(String(150), nullable=True)
    birth_year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    country: Mapped[str | None] = mapped_column(String(100), nullable=True)
    gender: Mapped[str | None] = mapped_column(String(100), nullable=True)

    living_situation: Mapped[str | None] = mapped_column(String(150), nullable=True)
    relationship_status: Mapped[str | None] = mapped_column(String(150), nullable=True)
    work_status: Mapped[str | None] = mapped_column(String(150), nullable=True)

    main_life_context: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)
    interests: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)

    preferred_reflection_style: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="balanced",
    )

    onboarding_completed: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
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