"""
MentorMemory — Long-Term AI Memory model.

One record represents one durable fact the AI Mentor remembers about a learner.
Memories are independent of conversations and survive conversation deletion.

Day 65 Part A1 — persistence layer.
Day 65 Part A2 — retrieval & injection layer.
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
    Index,
    Boolean,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


# ──────────────────────────────────────────────────────────────────────────────
# Enums
# ──────────────────────────────────────────────────────────────────────────────

class MemoryCategory(str, enum.Enum):
    """Category of a long-term memory. Extensible for future categories."""
    LEARNING_STYLE = "LEARNING_STYLE"
    LONG_TERM_GOAL = "LONG_TERM_GOAL"
    STRONG_TOPIC = "STRONG_TOPIC"
    WEAK_TOPIC = "WEAK_TOPIC"
    LEARNING_PREFERENCE = "LEARNING_PREFERENCE"
    FREQUENT_TOPIC = "FREQUENT_TOPIC"
    ACHIEVEMENT = "ACHIEVEMENT"
    PERSONAL_PREFERENCE = "PERSONAL_PREFERENCE"
    GENERAL = "GENERAL"


class MemoryImportance(str, enum.Enum):
    """Priority level of a memory — used for retrieval ranking."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class MemoryStatus(str, enum.Enum):
    """Lifecycle status. Memories are never permanently deleted by default."""
    ACTIVE = "ACTIVE"
    ARCHIVED = "ARCHIVED"


class MemorySource(str, enum.Enum):
    """Tracks how a memory was created — improves transparency."""
    CONVERSATION = "Conversation"
    AI_CONTEXT = "AI Context"
    LEARNING_SESSION = "Learning Session"
    SESSION_SUMMARY = "Session Summary"
    JOURNEY = "Journey"
    TOOL = "Tool"
    MANUAL = "Manual"


# ──────────────────────────────────────────────────────────────────────────────
# Model
# ──────────────────────────────────────────────────────────────────────────────

class MentorMemory(Base):
    """
    One persistent long-term memory belonging to exactly one user.

    Key relationships:
        User  1 ──── * MentorMemory

    No direct relationship with conversations.
    Memories survive conversation deletion.
    """

    __tablename__ = "mentor_memories"

    id: Mapped[int] = mapped_column(primary_key=True)

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    category: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default=MemoryCategory.GENERAL.value,
    )

    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    importance: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=MemoryImportance.MEDIUM.value,
    )

    source: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default=MemorySource.CONVERSATION.value,
    )

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=MemoryStatus.ACTIVE.value,
    )

    # Pinned memories receive retrieval priority (Part A2)
    is_pinned: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
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

    # Refreshed every time this memory participates in a mentor response
    last_used_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # ── Relationships ──────────────────────────────────────────────────────────

    user = relationship("User", back_populates="mentor_memories")

    # ── Indexes ────────────────────────────────────────────────────────────────

    __table_args__ = (
        Index("idx_memory_user_id", "user_id"),
        Index("idx_memory_category", "category"),
        Index("idx_memory_status", "status"),
        Index("idx_memory_importance", "importance"),
        Index("idx_memory_user_status", "user_id", "status"),
        Index("idx_memory_user_category", "user_id", "category"),
        Index("idx_memory_last_used", "last_used_at"),
    )
