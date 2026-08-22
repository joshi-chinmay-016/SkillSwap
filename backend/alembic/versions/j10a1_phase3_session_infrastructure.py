"""add phase 3 session infrastructure, feedback foreign key and unique constraints

Revision ID: j10a1_phase3_session_infra
Revises: i10a1_mentor_avail_date
Create Date: 2026-08-22 18:30:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'j10a1_phase3_session_infra'
down_revision = 'i10a1_mentor_avail_date'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Add created_at column if not exists
    op.execute(sa.text("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name='feedback' AND column_name='created_at'
            ) THEN
                ALTER TABLE feedback ADD COLUMN created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL;
            END IF;
        END $$;
    """))

    # 2. Update foreign key on feedback.session_id -> sessions.id
    op.execute(sa.text("""
        DO $$
        DECLARE
            fk_record RECORD;
        BEGIN
            FOR fk_record IN
                SELECT constraint_name
                FROM information_schema.table_constraints
                WHERE table_name = 'feedback' AND constraint_type = 'FOREIGN KEY'
            LOOP
                EXECUTE 'ALTER TABLE feedback DROP CONSTRAINT IF EXISTS ' || quote_ident(fk_record.constraint_name);
            END LOOP;

            IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'sessions') THEN
                ALTER TABLE feedback
                ADD CONSTRAINT feedback_session_id_fkey
                FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE;
            END IF;

            IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'users') THEN
                ALTER TABLE feedback
                ADD CONSTRAINT feedback_reviewer_id_fkey
                FOREIGN KEY (reviewer_id) REFERENCES users(id) ON DELETE CASCADE;

                ALTER TABLE feedback
                ADD CONSTRAINT feedback_reviewee_id_fkey
                FOREIGN KEY (reviewee_id) REFERENCES users(id) ON DELETE CASCADE;
            END IF;
        END $$;
    """))

    # 3. Deduplicate any existing feedback duplicates before creating unique constraint
    op.execute(sa.text("""
        DELETE FROM feedback a USING feedback b
        WHERE a.id < b.id AND a.session_id = b.session_id AND a.reviewer_id = b.reviewer_id;
    """))

    # 4. Add unique constraint (session_id, reviewer_id)
    op.execute(sa.text("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_constraint WHERE conname = 'uq_feedback_session_reviewer'
            ) THEN
                ALTER TABLE feedback ADD CONSTRAINT uq_feedback_session_reviewer UNIQUE (session_id, reviewer_id);
            END IF;
        END $$;
    """))

    # 5. Add index on sessions(status, scheduled_at)
    op.execute(sa.text("""
        CREATE INDEX IF NOT EXISTS idx_sessions_status_scheduled_at ON sessions(status, scheduled_at);
        CREATE INDEX IF NOT EXISTS idx_feedback_reviewee_rating ON feedback(reviewee_id, rating);
    """))


def downgrade() -> None:
    op.execute(sa.text("""
        DROP INDEX IF EXISTS idx_sessions_status_scheduled_at;
        DROP INDEX IF EXISTS idx_feedback_reviewee_rating;
        ALTER TABLE feedback DROP CONSTRAINT IF EXISTS uq_feedback_session_reviewer;
    """))
