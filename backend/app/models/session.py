from sqlalchemy import (
    ForeignKey,
    String,
    DateTime,
    Integer,
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


class Session(Base):

    __tablename__ = "sessions"

    id: Mapped[int] = mapped_column(
        primary_key=True
    )

    requester_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True
    )

    mentor_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True
    )

    skill_id: Mapped[int] = mapped_column(
        ForeignKey("skills.id", ondelete="CASCADE"),
        index=True
    )

    scheduled_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        index=True,
        nullable=False
    )

    duration_minutes: Mapped[int] = mapped_column(
        Integer,
        default=60,
        nullable=False
    )

    meeting_link: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    status: Mapped[str] = mapped_column(
        String(20),
        default="scheduled",
        nullable=False,
        index=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=sa.func.now(),
        nullable=False
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=sa.func.now(),
        onupdate=sa.func.now(),
        nullable=False
    )

    # Relationships
    requester = relationship(
        "User",
        foreign_keys=[requester_id],
        backref="requested_sessions"
    )

    mentor = relationship(
        "User",
        foreign_keys=[mentor_id],
        backref="mentored_sessions"
    )

    skill = relationship(
        "Skill",
        backref="sessions"
    )

    __table_args__ = (
        Index(
            "idx_sessions_mentor_status_scheduled",
            "mentor_id", "status", "scheduled_at"
        ),
        Index(
            "idx_sessions_requester_status_scheduled",
            "requester_id", "status", "scheduled_at"
        ),
    )