from sqlalchemy import (
    ForeignKey,
    String,
    Integer,
    DateTime,
    JSON,
    Index
)
import sqlalchemy as sa
from sqlalchemy.orm import (
    Mapped,
    mapped_column
)
from datetime import datetime

from app.models.base import Base


class LearningActivity(Base):
    __tablename__ = "learning_activities"

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

    activity_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False
    )

    entity_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False
    )

    entity_id: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )

    activity_data: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=sa.func.now(),
        nullable=False
    )

    __table_args__ = (
        Index("idx_learning_activities_user_created", "user_id", "created_at"),
        Index("idx_learning_activities_user_type_created", "user_id", "activity_type", "created_at"),
    )
