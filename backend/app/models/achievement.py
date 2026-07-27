from sqlalchemy import (
    String,
    Integer,
    DateTime,
)
import sqlalchemy as sa
from sqlalchemy.orm import (
    Mapped,
    mapped_column
)
from datetime import datetime

from app.models.base import Base


class Achievement(Base):
    __tablename__ = "achievements"

    id: Mapped[int] = mapped_column(
        primary_key=True
    )

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    description: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    category: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True
    )

    badge_tier: Mapped[str] = mapped_column(
        String(50),
        nullable=False
    )

    badge_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    icon: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    requirement_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False
    )

    requirement_value: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )

    xp_reward: Mapped[int] = mapped_column(
        Integer,
        default=50,
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
