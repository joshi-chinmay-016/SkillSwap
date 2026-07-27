from sqlalchemy import (
    ForeignKey,
    DateTime,
    UniqueConstraint,
    Index
)
from sqlalchemy.orm import (
    Mapped,
    mapped_column
)
from datetime import datetime

from app.models.base import Base


class UserAchievement(Base):
    __tablename__ = "user_achievements"

    id: Mapped[int] = mapped_column(
        primary_key=True
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey(
            "users.id",
            ondelete="CASCADE"
        ),
        index=True,
        nullable=False
    )

    achievement_id: Mapped[int] = mapped_column(
        ForeignKey(
            "achievements.id",
            ondelete="CASCADE"
        ),
        index=True,
        nullable=False
    )

    unlocked_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default="now()",
        nullable=False
    )

    __table_args__ = (
        UniqueConstraint("user_id", "achievement_id", name="uq_user_achievement"),
        Index("idx_user_achievements_user_ach", "user_id", "achievement_id"),
    )
