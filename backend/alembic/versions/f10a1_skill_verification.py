"""add skill verification and assessment

Revision ID: f10a1_skill_verification
Revises: f70a1_reconcile_feedback_fk
Create Date: 2026-08-20 16:35:00.000000

Day 78 Part A — Skill Verification & Evidence-Based Credibility Foundation
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers
revision: str = "f10a1_skill_verification"
down_revision: Union[str, None] = "f70a1_reconcile_feedback_fk"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add verification columns to user_skills if not exists
    try:
        op.add_column(
            "user_skills",
            sa.Column(
                "verification_status",
                sa.String(length=20),
                nullable=False,
                server_default="CLAIMED"
            )
        )
    except Exception:
        pass

    try:
        op.add_column(
            "user_skills",
            sa.Column(
                "claimed_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.func.now()
            )
        )
    except Exception:
        pass

    try:
        op.add_column(
            "user_skills",
            sa.Column(
                "verified_at",
                sa.DateTime(timezone=True),
                nullable=True
            )
        )
    except Exception:
        pass

    try:
        op.add_column(
            "user_skills",
            sa.Column(
                "score",
                sa.Float(),
                nullable=True
            )
        )
    except Exception:
        pass

    try:
        op.create_index(
            "idx_user_skill_verification_status",
            "user_skills",
            ["verification_status"]
        )
    except Exception:
        pass

    # Create assessment_questions table
    try:
        op.create_table(
            "assessment_questions",
            sa.Column("id", sa.Integer(), nullable=False, primary_key=True),
            sa.Column("skill_id", sa.Integer(), nullable=False),
            sa.Column("question_text", sa.Text(), nullable=False),
            sa.Column("options", sa.Text(), nullable=False), # JSON string of options
            sa.Column("correct_option", sa.Integer(), nullable=False),
            sa.Column("explanation", sa.Text(), nullable=True),
            sa.Column("difficulty", sa.String(length=20), nullable=False, server_default="INTERMEDIATE"),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.func.now(),
                nullable=False
            ),
            sa.ForeignKeyConstraint(["skill_id"], ["skills.id"], ondelete="CASCADE"),
        )
        op.create_index("idx_assessment_questions_skill_id", "assessment_questions", ["skill_id"])
    except Exception:
        pass

    # Create skill_assessment_results table
    try:
        op.create_table(
            "skill_assessment_results",
            sa.Column("id", sa.Integer(), nullable=False, primary_key=True),
            sa.Column("user_id", sa.Integer(), nullable=False),
            sa.Column("skill_id", sa.Integer(), nullable=False),
            sa.Column("user_skill_id", sa.Integer(), nullable=False),
            sa.Column("score", sa.Float(), nullable=False),
            sa.Column("passed", sa.Boolean(), nullable=False, server_default=sa.text("false")),
            sa.Column("total_questions", sa.Integer(), nullable=False),
            sa.Column("correct_answers", sa.Integer(), nullable=False),
            sa.Column("details", sa.Text(), nullable=True), # JSON string of response details
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.func.now(),
                nullable=False
            ),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["skill_id"], ["skills.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["user_skill_id"], ["user_skills.id"], ondelete="CASCADE"),
        )
        op.create_index("idx_skill_assessment_results_user_skill", "skill_assessment_results", ["user_id", "skill_id"])
    except Exception:
        pass


def downgrade() -> None:
    try:
        op.drop_index("idx_skill_assessment_results_user_skill", table_name="skill_assessment_results")
        op.drop_table("skill_assessment_results")
    except Exception:
        pass

    try:
        op.drop_index("idx_assessment_questions_skill_id", table_name="assessment_questions")
        op.drop_table("assessment_questions")
    except Exception:
        pass

    try:
        op.drop_index("idx_user_skill_verification_status", table_name="user_skills")
        op.drop_column("user_skills", "score")
        op.drop_column("user_skills", "verified_at")
        op.drop_column("user_skills", "claimed_at")
        op.drop_column("user_skills", "verification_status")
    except Exception:
        pass
