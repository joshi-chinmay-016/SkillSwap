from sqlalchemy import (
    ForeignKey,
    String,
    DateTime,
    Integer,
    Float,
    Boolean,
    func
)
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship
)
from datetime import datetime

from app.models.base import Base


class LearningJourney(Base):
    __tablename__ = "learning_journeys"

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

    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    target_role: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    description: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True
    )

    duration_months: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True
    )

    status: Mapped[str] = mapped_column(
        String(20),
        default="active",
        nullable=False
    )

    progress_percentage: Mapped[float] = mapped_column(
        Float,
        default=0.0,
        nullable=False
    )

    current_week: Mapped[int] = mapped_column(
        Integer,
        default=1,
        nullable=False
    )

    total_weeks: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )

    user = relationship(
        "User",
        back_populates="journeys"
    )

    milestones = relationship(
        "JourneyMilestone",
        back_populates="journey",
        cascade="all, delete-orphan",
        order_by="JourneyMilestone.week_number"
    )

    learning_sessions = relationship(
        "LearningSession",
        back_populates="journey",
        cascade="all, delete-orphan"
    )

    mentor_conversations = relationship(
        "MentorConversation",
        back_populates="journey",
        foreign_keys="MentorConversation.journey_id",
    )


class JourneyMilestone(Base):
    __tablename__ = "journey_milestones"

    id: Mapped[int] = mapped_column(
        primary_key=True
    )

    journey_id: Mapped[int] = mapped_column(
        ForeignKey(
            "learning_journeys.id",
            ondelete="CASCADE"
        ),
        index=True,
        nullable=False
    )

    week_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )

    topic: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    goal: Mapped[str] = mapped_column(
        String(500),
        nullable=False
    )

    status: Mapped[str] = mapped_column(
        String(20),
        default="pending",
        nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )

    journey = relationship(
        "LearningJourney",
        back_populates="milestones"
    )

    tasks = relationship(
        "JourneyTask",
        back_populates="milestone",
        cascade="all, delete-orphan"
    )


class JourneyTask(Base):
    __tablename__ = "journey_tasks"

    id: Mapped[int] = mapped_column(
        primary_key=True
    )

    milestone_id: Mapped[int] = mapped_column(
        ForeignKey(
            "journey_milestones.id",
            ondelete="CASCADE"
        ),
        index=True,
        nullable=False
    )

    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    description: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True
    )

    is_completed: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False
    )

    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )

    milestone = relationship(
        "JourneyMilestone",
        back_populates="tasks"
    )
