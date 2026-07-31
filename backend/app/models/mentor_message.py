"""
MentorMessage — individual message within a MentorConversation.

Supports two roles: USER and ASSISTANT.
System prompts are NEVER stored as MentorMessages.
"""
import enum
from datetime import datetime
from typing import Optional

import sqlalchemy as sa
from sqlalchemy import (
    ForeignKey,
    String,
    Text,
    DateTime,
    Integer,
    Index,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class MessageRole(str, enum.Enum):
    USER = "USER"
    ASSISTANT = "ASSISTANT"


class MentorMessage(Base):
    """
    One message within a MentorConversation.

    Rules:
        - role must be USER or ASSISTANT
        - content cannot be empty
        - system prompts are NEVER stored here
        - assistant messages are created internally — never by the frontend
    """

    __tablename__ = "mentor_messages"

    id: Mapped[int] = mapped_column(primary_key=True)

    conversation_id: Mapped[int] = mapped_column(
        ForeignKey("mentor_conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    role: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=sa.func.now(),
        nullable=False,
    )

    # ── Relationships ──────────────────────────────────────────────────────────

    conversation = relationship(
        "MentorConversation",
        back_populates="messages",
    )

    # ── Indexes ────────────────────────────────────────────────────────────────

    __table_args__ = (
        Index("idx_mentor_msg_conversation_id", "conversation_id"),
        Index("idx_mentor_msg_created_at", "created_at"),
        # Efficient "get messages for a conversation in order"
        Index("idx_mentor_msg_conv_created", "conversation_id", "created_at"),
    )
