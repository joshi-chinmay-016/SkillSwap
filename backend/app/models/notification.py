from sqlalchemy import (
    ForeignKey,
    String,
    Boolean,
    DateTime,
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


class Notification(Base):

    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(
        primary_key=True
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True
    )

    type: Mapped[str] = mapped_column(
        String(50),
        default="GENERAL",
        nullable=False,
        index=True
    )

    title: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True
    )

    message: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    related_session_id: Mapped[int | None] = mapped_column(
        ForeignKey("sessions.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )

    is_read: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        index=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=sa.func.now(),
        nullable=False
    )

    # Relationships
    user = relationship(
        "User",
        backref="notifications"
    )

    session = relationship(
        "Session",
        foreign_keys=[related_session_id]
    )

    __table_args__ = (
        Index(
            "idx_notifications_user_unread_created",
            "user_id", "is_read", "created_at"
        ),
    )