"""add started_at and completed_at to sessions table for phase 5 duration tracking

Revision ID: l10a1_phase5_session_realtime
Revises: k10a1_phase4_session_intel
Create Date: 2026-08-23 18:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'l10a1_phase5_session_realtime'
down_revision = 'k10a1_phase4_session_intel'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(sa.text("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name='sessions' AND column_name='started_at'
            ) THEN
                ALTER TABLE sessions ADD COLUMN started_at TIMESTAMP WITH TIME ZONE;
            END IF;

            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name='sessions' AND column_name='completed_at'
            ) THEN
                ALTER TABLE sessions ADD COLUMN completed_at TIMESTAMP WITH TIME ZONE;
            END IF;
        END $$;
    """))


def downgrade() -> None:
    op.execute(sa.text("""
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name='sessions' AND column_name='started_at'
            ) THEN
                ALTER TABLE sessions DROP COLUMN started_at;
            END IF;

            IF EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name='sessions' AND column_name='completed_at'
            ) THEN
                ALTER TABLE sessions DROP COLUMN completed_at;
            END IF;
        END $$;
    """))
