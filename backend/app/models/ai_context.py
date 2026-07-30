import uuid as uuid_lib
from datetime import datetime
from typing import List, Optional

import sqlalchemy as sa
from sqlalchemy import (
    ForeignKey,
    String,
    Text,
    DateTime,
    JSON,
    Integer,
    Index,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class AIContext(Base):
    """
    Persistent AI Context model for a user's accumulated learning profile.

    Stores strengths, weaknesses, learning interests, recommendations,
    and style gathered across completed sessions.
    """

    __tablename__ = "ai_contexts"

    id: Mapped[int] = mapped_column(primary_key=True)

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )

    overall_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    strong_topics: Mapped[Optional[List[str]]] = mapped_column(
        JSON, nullable=False, default=list
    )

    weak_topics: Mapped[Optional[List[str]]] = mapped_column(
        JSON, nullable=False, default=list
    )

    learning_interests: Mapped[Optional[List[str]]] = mapped_column(
        JSON, nullable=False, default=list
    )

    recommended_topics: Mapped[Optional[List[str]]] = mapped_column(
        JSON, nullable=False, default=list
    )

    learning_style: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    completed_sessions: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0
    )

    context_version: Mapped[int] = mapped_column(
        Integer, nullable=False, default=1
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

    user = relationship("User", backref="ai_context", uselist=False)

    __table_args__ = (
        Index("idx_ai_contexts_user_id", "user_id"),
    )
