import sqlalchemy as sa
from sqlalchemy import (
    ForeignKey,
    String,
    Text,
    DateTime,
    JSON,
    Index
)
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship
)
from datetime import datetime
from typing import List, Optional

from app.models.base import Base


class SessionIntelligence(Base):
    """
    Authoritative post-session intelligence record for peer-learning sessions.
    Contains grounded AI summary, extracted skills, takeaways, and provenance metadata.
    """
    __tablename__ = "session_intelligence"

    id: Mapped[int] = mapped_column(
        primary_key=True
    )

    session_id: Mapped[int] = mapped_column(
        ForeignKey("sessions.id", ondelete="CASCADE"),
        unique=True,
        index=True,
        nullable=False
    )

    status: Mapped[str] = mapped_column(
        String(30),
        default="completed",  # "completed", "insufficient_data", "failed"
        nullable=False
    )

    summary: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    topics_covered: Mapped[Optional[List]] = mapped_column(
        JSON,
        nullable=False,
        default=list
    )

    skills_taught: Mapped[Optional[List]] = mapped_column(
        JSON,
        nullable=False,
        default=list
    )

    skills_learned: Mapped[Optional[List]] = mapped_column(
        JSON,
        nullable=False,
        default=list
    )

    key_takeaways: Mapped[Optional[List]] = mapped_column(
        JSON,
        nullable=False,
        default=list
    )

    mentor_notes_summary: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    learner_notes_summary: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    recommended_next_steps: Mapped[Optional[List]] = mapped_column(
        JSON,
        nullable=False,
        default=list
    )

    provenance: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        default=dict  # {"provider": "gemini", "model": "gemini-1.5-flash", "signals": ["notes", "topics"], "generated_at": ...}
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

    # One-to-one relationship back to Session
    session = relationship(
        "Session",
        back_populates="intelligence"
    )

    __table_args__ = (
        Index("idx_session_intelligence_session_status", "session_id", "status"),
    )
