import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, SmallInteger, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class UserContext(Base):
    __tablename__ = "user_contexts"

    __table_args__ = (
        CheckConstraint(
            "age_range_min >= 13",
            name="ck_user_context_age_min_lower_bound",
        ),
        CheckConstraint(
            "age_range_max <= 120",
            name="ck_user_context_age_max_upper_bound",
        ),
        CheckConstraint(
            "age_range_min <= age_range_max",
            name="ck_user_context_age_range_order",
        ),
        CheckConstraint(
            "family_support_score >= 0 AND family_support_score <= 10",
            name="ck_user_context_family_support_score_range",
        ),
        CheckConstraint(
            "social_connection_score >= 0 AND social_connection_score <= 10",
            name="ck_user_context_social_connection_score_range",
        ),
        CheckConstraint(
            "work_stress_baseline >= 0 AND work_stress_baseline <= 10",
            name="ck_user_context_work_stress_baseline_range",
        ),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )

    age_range_min: Mapped[int] = mapped_column(Integer, nullable=False)
    age_range_max: Mapped[int] = mapped_column(Integer, nullable=False)

    country: Mapped[str] = mapped_column(String(100), nullable=False)

    work_situation: Mapped[str] = mapped_column(String(50), nullable=False)
    relationship_status: Mapped[str] = mapped_column(String(50), nullable=False)

    family_support_score: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    social_connection_score: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    work_stress_baseline: Mapped[int] = mapped_column(SmallInteger, nullable=False)

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