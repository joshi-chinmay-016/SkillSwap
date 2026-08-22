import sqlalchemy as sa
from sqlalchemy import (
    ForeignKey,
    String,
    DateTime,
    Float,
    Index
)
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship
)
from datetime import datetime

from app.models.base import Base


class SessionTopic(Base):
    """
    Specific discussion topics and skills covered during a session.
    """
    __tablename__ = "session_topics"

    id: Mapped[int] = mapped_column(
        primary_key=True
    )

    session_id: Mapped[int] = mapped_column(
        ForeignKey("sessions.id", ondelete="CASCADE"),
        index=True,
        nullable=False
    )

    topic_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    skill_id: Mapped[int | None] = mapped_column(
        ForeignKey("skills.id", ondelete="SET NULL"),
        index=True,
        nullable=True
    )

    source: Mapped[str] = mapped_column(
        String(30),
        default="user_input",  # "user_input" or "ai_extracted"
        nullable=False
    )

    confidence: Mapped[float] = mapped_column(
        Float,
        default=1.0,
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
        back_populates="topics"
    )

    skill = relationship(
        "Skill",
        backref="session_topics"
    )

    __table_args__ = (
        Index("idx_session_topics_session_name", "session_id", "topic_name"),
    )
