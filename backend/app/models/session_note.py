import sqlalchemy as sa
from sqlalchemy import (
    ForeignKey,
    String,
    DateTime,
    JSON,
    UniqueConstraint,
    Index
)
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship
)
from datetime import datetime

from app.models.base import Base


class SessionNote(Base):
    """
    Real notes, questions, and takeaways captured by a participant during/after a session.
    """
    __tablename__ = "session_notes"

    id: Mapped[int] = mapped_column(
        primary_key=True
    )

    session_id: Mapped[int] = mapped_column(
        ForeignKey("sessions.id", ondelete="CASCADE"),
        index=True,
        nullable=False
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False
    )

    role: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="learner"  # "learner" or "mentor"
    )

    notes_data: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        default=dict  # {"questions": [], "concepts": [], "struggles": [], "takeaways": [], "resources": [], "next_steps": []}
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
    session = relationship(
        "Session",
        back_populates="notes"
    )

    user = relationship(
        "User",
        backref="session_notes"
    )

    __table_args__ = (
        UniqueConstraint("session_id", "user_id", name="uq_session_notes_session_user"),
        Index("idx_session_notes_session_role", "session_id", "role"),
    )
