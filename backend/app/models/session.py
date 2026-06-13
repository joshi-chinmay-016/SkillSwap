from sqlalchemy import (
    ForeignKey,
    String,
    DateTime
)

from sqlalchemy.orm import (
    Mapped,
    mapped_column
)

from datetime import datetime

from app.models.base import Base


class Session(Base):

    __tablename__ = "sessions"

    id: Mapped[int] = mapped_column(
        primary_key=True
    )

    requester_id: Mapped[int] = mapped_column(
        ForeignKey("users.id")
    )

    mentor_id: Mapped[int] = mapped_column(
        ForeignKey("users.id")
    )

    skill_id: Mapped[int] = mapped_column(
        ForeignKey("skills.id")
    )

    scheduled_at: Mapped[datetime] = mapped_column(
        DateTime
    )

    meeting_link: Mapped[str] = mapped_column(
        String(255)
    )

    status: Mapped[str] = mapped_column(
        String(20),
        default="scheduled"
    )