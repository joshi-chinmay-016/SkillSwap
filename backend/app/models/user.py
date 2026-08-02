from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)

    name: Mapped[str] = mapped_column(String(100))

    email: Mapped[str] = mapped_column(
        String(255),
        unique=True
    )

    password_hash: Mapped[str] = mapped_column(
        String(255)
    )

    oauth_provider: Mapped[str] = mapped_column(
        String(50),
        nullable=True
    )

    profile = relationship(
        "Profile",
        back_populates="user"
    )

    user_skills = relationship(
        "UserSkill",
        back_populates="user"
    )

    journeys = relationship(
        "LearningJourney",
        back_populates="user",
        cascade="all, delete-orphan"
    )

    learning_sessions = relationship(
        "LearningSession",
        back_populates="user",
        cascade="all, delete-orphan"
    )

    mentor_conversations = relationship(
        "MentorConversation",
        back_populates="user",
        cascade="all, delete-orphan"
    )

    mentor_memories = relationship(
        "MentorMemory",
        back_populates="user",
        cascade="all, delete-orphan"
    )