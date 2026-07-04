from datetime import datetime

from sqlalchemy import (
    Float,
    ForeignKey,
    DateTime,
    CheckConstraint
)

from sqlalchemy.orm import (
    Mapped,
    mapped_column
)

from app.models.base import Base


class MentorFundamentals(Base):

    __tablename__ = "mentor_fundamentals"

    __table_args__ = (
        CheckConstraint(
            "rating_score >= 0 AND rating_score <= 100",
            name="ck_rating_score"
        ),
        CheckConstraint(
            "completion_score >= 0 AND completion_score <= 100",
            name="ck_completion_score"
        ),
        CheckConstraint(
            "response_score >= 0 AND response_score <= 100",
            name="ck_response_score"
        ),
        CheckConstraint(
            "activity_score >= 0 AND activity_score <= 100",
            name="ck_activity_score"
        ),
        CheckConstraint(
            "fundamentals_score >= 0 AND fundamentals_score <= 100",
            name="ck_fundamentals_score"
        ),
    )

    id: Mapped[int] = mapped_column(
        primary_key=True
    )

    mentor_id: Mapped[int] = mapped_column(
        ForeignKey(
            "users.id",
            ondelete="CASCADE"
        ),
        unique=True,
        index=True,
        nullable=False
    )

    rating_score: Mapped[float] = mapped_column(
        Float,
        default=0.0,
        nullable=False
    )

    completion_score: Mapped[float] = mapped_column(
        Float,
        default=0.0,
        nullable=False
    )

    response_score: Mapped[float] = mapped_column(
        Float,
        default=0.0,
        nullable=False
    )

    activity_score: Mapped[float] = mapped_column(
        Float,
        default=0.0,
        nullable=False
    )

    fundamentals_score: Mapped[float] = mapped_column(
        Float,
        default=0.0,
        nullable=False
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )