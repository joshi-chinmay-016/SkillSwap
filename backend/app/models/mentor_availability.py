from sqlalchemy import (
    ForeignKey,
    String,
    Time
)

from sqlalchemy.orm import (
    Mapped,
    mapped_column
)

from datetime import time

from app.models.base import Base


class MentorAvailability(Base):

    __tablename__ = "mentor_availability"

    id: Mapped[int] = mapped_column(
        primary_key=True
    )

    mentor_id: Mapped[int] = mapped_column(
        ForeignKey("users.id")
    )

    day_of_week: Mapped[str] = mapped_column(
        String(20)
    )

    start_time: Mapped[time] = mapped_column(
        Time
    )

    end_time: Mapped[time] = mapped_column(
        Time
    )