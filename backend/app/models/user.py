from sqlalchemy import String, Boolean, text
import sqlalchemy as sa
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

    role: Mapped[str] = mapped_column(
        String(20),
        default="USER",
        server_default="USER",
        index=True
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        server_default=sa.text("true"),
        index=True
    )

    oauth_provider: Mapped[str] = mapped_column(
        String(50),
        nullable=True
    )

    profile = relationship(
        "Profile",
        back_populates="user",
        uselist=False
    )

    user_skills = relationship(
        "UserSkill",
        back_populates="user"
    )

    oauth_identities = relationship(
        "OAuthIdentity",
        back_populates="user",
        cascade="all, delete-orphan"
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

    documents = relationship(
        "Document",
        back_populates="user",
        cascade="all, delete-orphan"
    )