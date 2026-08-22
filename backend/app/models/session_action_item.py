import sqlalchemy as sa
from sqlalchemy import (
    ForeignKey,
    String,
    Text,
    DateTime,
    Index
)
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship
)
from datetime import datetime

from app.models.base import Base


class SessionActionItem(Base):
    """
    Actionable next steps, homework, and practice tasks derived from a session.
    """
    __tablename__ = "session_action_items"

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
        nullable=False  # Owner of the action item
    )

    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    status: Mapped[str] = mapped_column(
        String(20),
        default="pending",  # "pending" or "completed"
        nullable=False
    )

    source: Mapped[str] = mapped_column(
        String(30),
        default="user_input",  # "user_input" or "ai_extracted"
        nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=sa.func.now(),
        nullable=False
    )

    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )

    # Relationships
    session = relationship(
        "Session",
        back_populates="action_items"
    )

    user = relationship(
        "User",
        backref="session_action_items"
    )

    __table_args__ = (
        Index("idx_session_actions_session_user_status", "session_id", "user_id", "status"),
    )
