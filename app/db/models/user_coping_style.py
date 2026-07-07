import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, SmallInteger, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class UserCopingStyle(Base):
    __tablename__ = "user_coping_styles"

    __table_args__ = (
        CheckConstraint(
            "writing_preference_score >= 0 AND writing_preference_score <= 10",
            name="ck_user_coping_styles_writing_score_range",
        ),
        CheckConstraint(
            "movement_preference_score >= 0 AND movement_preference_score <= 10",
            name="ck_user_coping_styles_movement_score_range",
        ),
        CheckConstraint(
            "breathing_preference_score >= 0 AND breathing_preference_score <= 10",
            name="ck_user_coping_styles_breathing_score_range",
        ),
        CheckConstraint(
            "social_support_preference_score >= 0 AND social_support_preference_score <= 10",
            name="ck_user_coping_styles_social_support_score_range",
        ),
        CheckConstraint(
            "reflection_preference_score >= 0 AND reflection_preference_score <= 10",
            name="ck_user_coping_styles_reflection_score_range",
        ),
        CheckConstraint(
            "structure_preference_score >= 0 AND structure_preference_score <= 10",
            name="ck_user_coping_styles_structure_score_range",
        ),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )

    preferred_coping_styles: Mapped[list[str] | None] = mapped_column(
        JSONB,
        nullable=True,
    )

    disliked_coping_styles: Mapped[list[str] | None] = mapped_column(
        JSONB,
        nullable=True,
    )

    writing_preference_score: Mapped[int] = mapped_column(
        SmallInteger,
        nullable=False,
        default=5,
    )

    movement_preference_score: Mapped[int] = mapped_column(
        SmallInteger,
        nullable=False,
        default=5,
    )

    breathing_preference_score: Mapped[int] = mapped_column(
        SmallInteger,
        nullable=False,
        default=5,
    )

    social_support_preference_score: Mapped[int] = mapped_column(
        SmallInteger,
        nullable=False,
        default=5,
    )

    reflection_preference_score: Mapped[int] = mapped_column(
        SmallInteger,
        nullable=False,
        default=5,
    )

    structure_preference_score: Mapped[int] = mapped_column(
        SmallInteger,
        nullable=False,
        default=5,
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