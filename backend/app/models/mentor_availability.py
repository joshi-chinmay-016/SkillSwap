from sqlalchemy import (
    ForeignKey,
    String,
    Time,
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

from datetime import time, datetime

from app.models.base import Base


class MentorAvailability(Base):

    __tablename__ = "mentor_availability"

    id: Mapped[int] = mapped_column(
        primary_key=True
    )

    mentor_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True
    )

    day_of_week: Mapped[str] = mapped_column(
        String(20),
        index=True
    )

    start_time: Mapped[time] = mapped_column(
        Time
    )

    end_time: Mapped[time] = mapped_column(
        Time
    )

    timezone: Mapped[str] = mapped_column(
        String(50),
        default="UTC",
        nullable=False
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False
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
    mentor = relationship(
        "User",
        backref="availabilities"
    )

    __table_args__ = (
        Index(
            "idx_mentor_availability_lookup",
            "mentor_id", "day_of_week", "is_active"
        ),
    )