from sqlalchemy import (
    ForeignKey,
    String,
    Integer,
    DateTime,
    UniqueConstraint,
    Index
)
import sqlalchemy as sa
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship
)
from datetime import datetime

from app.models.base import Base


class Feedback(Base):

    __tablename__ = "feedback"

    id: Mapped[int] = mapped_column(
        primary_key=True
    )

    session_id: Mapped[int] = mapped_column(
        ForeignKey("sessions.id", ondelete="CASCADE"),
        index=True,
        nullable=False
    )

    reviewer_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False
    )

    reviewee_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False
    )

    rating: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )

    comment: Mapped[str] = mapped_column(
        String(500),
        nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=sa.func.now(),
        nullable=False
    )

    # Relationships
    session = relationship(
        "Session",
        back_populates="feedbacks"
    )

    reviewer = relationship(
        "User",
        foreign_keys=[reviewer_id],
        backref="given_feedbacks"
    )

    reviewee = relationship(
        "User",
        foreign_keys=[reviewee_id],
        backref="received_feedbacks"
    )

    __table_args__ = (
        UniqueConstraint("session_id", "reviewer_id", name="uq_feedback_session_reviewer"),
        Index("idx_feedback_reviewee_rating", "reviewee_id", "rating"),
    )