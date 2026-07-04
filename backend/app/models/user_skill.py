from sqlalchemy import (ForeignKey,String,Index)

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
)