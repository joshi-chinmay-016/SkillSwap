import uuid as uuid_lib

from sqlalchemy import (
    ForeignKey,
    String,
    Text,
    DateTime,
    JSON,
    Index,
    UniqueConstraint,
)
import sqlalchemy as sa
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)
from datetime import datetime
from typing import List, Optional

from app.models.base import Base


class SessionSummary(Base):
    """
    Persistent AI-generated summary for a completed LearningSession.

    Represents the structured learning outcomes of a session:
    - What the learner accomplished (summary)
    - Key concepts covered (key_takeaways)
    - What the learner did well (strengths)
    - What needs improvement (weaknesses)
    - What to study next (follow_up_topics)

    This is the canonical AI artifact for each session and will power:
    - Context-Aware AI Mentor (Day 62)
    - Conversation Memory (Day 63)
    - Long-Term Learning Profile (Day 65)
    - RAG Context (Day 74)
    """

    __tablename__ = "session_summaries"

    id: Mapped[int] = mapped_column(
        primary_key=True
    )

    uuid: Mapped[str] = mapped_column(
        String(36),
        unique=True,
        nullable=False,
        default=lambda: str(uuid_lib.uuid4()),
        index=True
    )

    # One-to-one FK — a summary cannot exist without a session
    session_id: Mapped[int] = mapped_column(
        ForeignKey(
            "learning_sessions.id",
            ondelete="CASCADE"
        ),
        unique=True,   # Enforces one-to-one at DB level
        nullable=False,
        index=True
    )

    # Core summary text
    summary: Mapped[str] = mapped_column(
        Text,
        nullable=False
    )

    # Structured JSON fields — avoid comma-separated strings
    key_takeaways: Mapped[Optional[List]] = mapped_column(
        JSON,
        nullable=False,
        default=list
    )

    strengths: Mapped[Optional[List]] = mapped_column(
        JSON,
        nullable=False,
        default=list
    )

    weaknesses: Mapped[Optional[List]] = mapped_column(
        JSON,
        nullable=False,
        default=list
    )

    follow_up_topics: Mapped[Optional[List]] = mapped_column(
        JSON,
        nullable=False,
        default=list
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

    # One-to-one relationship back to LearningSession
    session = relationship(
        "LearningSession",
        back_populates="summary"
    )

    __table_args__ = (
        Index(
            "idx_session_summaries_session_id",
            "session_id"
        ),
        Index(
            "idx_session_summaries_created_at",
            "created_at"
        ),
    )
