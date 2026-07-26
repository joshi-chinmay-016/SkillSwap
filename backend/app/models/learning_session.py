import uuid as uuid_lib

from sqlalchemy import (
    ForeignKey,
    String,
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


class LearningSession(Base):
    __tablename__ = "learning_sessions"

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

    user_id: Mapped[int] = mapped_column(
        ForeignKey(
            "users.id",
            ondelete="CASCADE"
        ),
        index=True,
        nullable=False
    )

    journey_id: Mapped[int] = mapped_column(
        ForeignKey(
            "learning_journeys.id",
            ondelete="CASCADE"
        ),
        index=True,
        nullable=False
    )

    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    status: Mapped[str] = mapped_column(
        String(20),
        default="ACTIVE",
        nullable=False
    )

    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=sa.func.now(),
        nullable=False
    )

    ended_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True
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
    user = relationship(
        "User",
        back_populates="learning_sessions"
    )

    journey = relationship(
        "LearningJourney",
        back_populates="learning_sessions"
    )

    __table_args__ = (
        Index(
            "idx_learning_sessions_user_status",
            "user_id", "status"
        ),
        Index(
            "idx_learning_sessions_journey_status",
            "journey_id", "status"
        ),
        Index(
            "idx_learning_sessions_user_created",
            "user_id", "created_at"
        ),
    )
