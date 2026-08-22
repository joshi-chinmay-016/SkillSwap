from sqlalchemy import (
    ForeignKey,
    String,
    Time,
    Date,
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

from datetime import time, datetime, date
from typing import Optional

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

    # Day of week (e.g. "Monday", "Tuesday", etc.) - auto-derived if specific_date is provided
    day_of_week: Mapped[str] = mapped_column(
        String(20),
        index=True
    )

    # Optional specific calendar date (NULL for recurring weekly schedule)
    specific_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
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
        Index(
            "idx_mentor_avail_date_lookup",
            "mentor_id", "specific_date", "is_active"
        ),
    )