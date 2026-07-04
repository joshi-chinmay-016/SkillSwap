from sqlalchemy import (
    ForeignKey,
    String,
    Integer
)

from sqlalchemy.orm import (
    Mapped,
    mapped_column
)

from app.models.base import Base


class Feedback(Base):

    __tablename__ = "feedback"

    id: Mapped[int] = mapped_column(
        primary_key=True
    )

    session_id: Mapped[int] = mapped_column(
        ForeignKey("sessions.id")
    )

    reviewer_id: Mapped[int] = mapped_column(
        ForeignKey("users.id")
    )

    reviewee_id: Mapped[int] = mapped_column(
        ForeignKey("users.id")
    )

    rating: Mapped[int] = mapped_column(
        Integer
    )

    comment: Mapped[str] = mapped_column(
        String(500)
    )