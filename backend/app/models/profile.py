from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

class Profile(Base):
    __tablename__ = "profiles"

    id: Mapped[int] = mapped_column(
        primary_key=True
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id")
    )

    bio: Mapped[str] = mapped_column(
        Text,
        nullable=True
    )

    department: Mapped[str] = mapped_column(
        String(100),
        nullable=True
    )

    year: Mapped[int] = mapped_column(
        nullable=True
    )

    avatar_url: Mapped[str] = mapped_column(
        Text,
        nullable=True
    )


    user = relationship(
        "User",
        back_populates="profile"
    )