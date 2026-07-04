from sqlalchemy import (
    ForeignKey,
    String,
    Boolean
)

from sqlalchemy.orm import (
    Mapped,
    mapped_column
)

from app.models.base import Base


class Notification(Base):

    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(
        primary_key=True
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id")
    )

    message: Mapped[str] = mapped_column(
        String(255)
    )

    is_read: Mapped[bool] = mapped_column(
        Boolean,
        default=False
    )