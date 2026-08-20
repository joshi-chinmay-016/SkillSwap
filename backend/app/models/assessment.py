from datetime import datetime
import json
from sqlalchemy import (
    ForeignKey,
    String,
    Text,
    Integer,
    Float,
    Boolean,
    DateTime,
    Index
)
import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class AssessmentQuestion(Base):
    __tablename__ = "assessment_questions"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True
    )

    skill_id: Mapped[int] = mapped_column(
        ForeignKey("skills.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    question_text: Mapped[str] = mapped_column(
        Text,
        nullable=False
    )

    options: Mapped[str] = mapped_column(
        Text,
        nullable=False
    )  # JSON formatted list of option strings

    correct_option: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )  # 0-indexed integer

    explanation: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    difficulty: Mapped[str] = mapped_column(
        String(20),
        default="INTERMEDIATE",
        server_default="INTERMEDIATE",
        nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=sa.func.now(),
        nullable=False
    )

    skill = relationship("Skill")

    def get_options_list(self) -> list[str]:
        try:
            return json.loads(self.options)
        except Exception:
            return []


class SkillAssessmentResult(Base):
    __tablename__ = "skill_assessment_results"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )

    skill_id: Mapped[int] = mapped_column(
        ForeignKey("skills.id", ondelete="CASCADE"),
        nullable=False
    )

    user_skill_id: Mapped[int] = mapped_column(
        ForeignKey("user_skills.id", ondelete="CASCADE"),
        nullable=False
    )

    score: Mapped[float] = mapped_column(
        Float,
        nullable=False
    )

    passed: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False
    )

    total_questions: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )

    correct_answers: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )

    details: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )  # JSON string of responses

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=sa.func.now(),
        nullable=False
    )

    user = relationship("User")
    skill = relationship("Skill")
    user_skill = relationship("UserSkill")

    __table_args__ = (
        Index(
            "idx_skill_assessment_results_user_skill",
            "user_id",
            "skill_id"
        ),
    )
