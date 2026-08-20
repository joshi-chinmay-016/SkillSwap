from datetime import datetime
from sqlalchemy import ForeignKey, String, Float, DateTime, Index
import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

class UserSkill(Base):
    __tablename__ = "user_skills"

    id: Mapped[int] = mapped_column(
        primary_key=True
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id")
    )

    skill_id: Mapped[int] = mapped_column(
        ForeignKey("skills.id")
    )

    type: Mapped[str] = mapped_column(
        String(20)
    )

    verification_status: Mapped[str] = mapped_column(
        String(20),
        default="CLAIMED",
        server_default="CLAIMED"
    )

    claimed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=sa.func.now()
    )

    verified_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )

    score: Mapped[float | None] = mapped_column(
        Float,
        nullable=True
    )

    user = relationship(
        "User",
        back_populates="user_skills"
    )
    skill = relationship(
        "Skill"
    )

    __table_args__ = (
        Index(
            "idx_user_skill_user_id",
            "user_id"
        ),
        Index(
            "idx_user_skill_skill_id",
            "skill_id"
        ),
        Index(
            "idx_user_skill_type",
            "type"
        ),
        Index(
            "idx_user_skill_verification_status",
            "verification_status"
        ),
    )