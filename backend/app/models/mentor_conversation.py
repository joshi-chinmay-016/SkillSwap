"""
MentorConversation — persistent AI Mentor conversation model.

A conversation belongs to exactly one user and contains zero or more
MentorMessages. It may optionally be associated with a LearningJourney
and/or a LearningSession (neither is required).

Day 63 Part A1 — persistence layer only.
Day 63 Part A2 — chat integration uses this model.
"""
import enum
from datetime import datetime
from typing import List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.mentor_message import MentorMessage

import sqlalchemy as sa
from sqlalchemy import (
    ForeignKey,
    String,
    Text,
    DateTime,
    Index,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class ConversationStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    ARCHIVED = "ARCHIVED"


class MentorConversation(Base):
    """
    One persistent AI Mentor conversation thread.

    Key relationships:
        User          1 ──── * MentorConversation
        MentorConversation 1 ──── * MentorMessage

    Optional contextual links:
        LearningJourney  1 ──── * MentorConversation
        LearningSession  1 ──── * MentorConversation
    """

    __tablename__ = "mentor_conversations"

    id: Mapped[int] = mapped_column(primary_key=True)

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Optional association with a Learning Journey
    journey_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("learning_journeys.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Optional association with a Learning Session
    session_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("learning_sessions.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        default="New Conversation",
    )

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=ConversationStatus.ACTIVE.value,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=sa.func.now(),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=sa.func.now(),
        onupdate=sa.func.now(),
        nullable=False,
    )

    # Updated whenever a message is added — drives conversation list ordering
    last_message_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # ── Relationships ──────────────────────────────────────────────────────────

    user = relationship("User", back_populates="mentor_conversations")

    journey = relationship(
        "LearningJourney",
        back_populates="mentor_conversations",
        foreign_keys=[journey_id],
    )

    session = relationship(
        "LearningSession",
        back_populates="mentor_conversations",
        foreign_keys=[session_id],
    )

    messages: Mapped[List["MentorMessage"]] = relationship(
        "MentorMessage",
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="MentorMessage.created_at.asc()",
    )

    # ── Indexes ────────────────────────────────────────────────────────────────

    __table_args__ = (
        Index("idx_mentor_conv_user_id", "user_id"),
        Index("idx_mentor_conv_status", "status"),
        Index("idx_mentor_conv_last_msg", "last_message_at"),
        Index("idx_mentor_conv_created", "created_at"),
        # Efficient "get my recent conversations"
        Index("idx_mentor_conv_user_last_msg", "user_id", "last_message_at"),
    )
