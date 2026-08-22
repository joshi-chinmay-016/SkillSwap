"""create phase 4 session notes, topics, action items, and session intelligence tables

Revision ID: k10a1_phase4_session_intelligence
Revises: j10a1_phase3_session_infra
Create Date: 2026-08-22 20:30:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'k10a1_phase4_session_intel'
down_revision = 'j10a1_phase3_session_infra'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. session_notes table
    op.execute(sa.text("""
        CREATE TABLE IF NOT EXISTS session_notes (
            id SERIAL PRIMARY KEY,
            session_id INTEGER NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            role VARCHAR(20) NOT NULL DEFAULT 'learner',
            notes_data JSONB NOT NULL DEFAULT '{}'::jsonb,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
            CONSTRAINT uq_session_notes_session_user UNIQUE (session_id, user_id)
        );
        CREATE INDEX IF NOT EXISTS idx_session_notes_session_id ON session_notes(session_id);
        CREATE INDEX IF NOT EXISTS idx_session_notes_user_id ON session_notes(user_id);
        CREATE INDEX IF NOT EXISTS idx_session_notes_session_role ON session_notes(session_id, role);
    """))

    # 2. session_topics table
    op.execute(sa.text("""
        CREATE TABLE IF NOT EXISTS session_topics (
            id SERIAL PRIMARY KEY,
            session_id INTEGER NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
            topic_name VARCHAR(100) NOT NULL,
            skill_id INTEGER REFERENCES skills(id) ON DELETE SET NULL,
            source VARCHAR(30) NOT NULL DEFAULT 'user_input',
            confidence FLOAT NOT NULL DEFAULT 1.0,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_session_topics_session_id ON session_topics(session_id);
        CREATE INDEX IF NOT EXISTS idx_session_topics_session_name ON session_topics(session_id, topic_name);
    """))

    # 3. session_action_items table
    op.execute(sa.text("""
        CREATE TABLE IF NOT EXISTS session_action_items (
            id SERIAL PRIMARY KEY,
            session_id INTEGER NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            title VARCHAR(255) NOT NULL,
            description TEXT,
            status VARCHAR(20) NOT NULL DEFAULT 'pending',
            source VARCHAR(30) NOT NULL DEFAULT 'user_input',
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
            completed_at TIMESTAMP WITH TIME ZONE
        );
        CREATE INDEX IF NOT EXISTS idx_session_actions_session_id ON session_action_items(session_id);
        CREATE INDEX IF NOT EXISTS idx_session_actions_user_id ON session_action_items(user_id);
        CREATE INDEX IF NOT EXISTS idx_session_actions_session_user_status ON session_action_items(session_id, user_id, status);
    """))

    # 4. session_intelligence table
    op.execute(sa.text("""
        CREATE TABLE IF NOT EXISTS session_intelligence (
            id SERIAL PRIMARY KEY,
            session_id INTEGER NOT NULL UNIQUE REFERENCES sessions(id) ON DELETE CASCADE,
            status VARCHAR(30) NOT NULL DEFAULT 'completed',
            summary TEXT,
            topics_covered JSONB NOT NULL DEFAULT '[]'::jsonb,
            skills_taught JSONB NOT NULL DEFAULT '[]'::jsonb,
            skills_learned JSONB NOT NULL DEFAULT '[]'::jsonb,
            key_takeaways JSONB NOT NULL DEFAULT '[]'::jsonb,
            mentor_notes_summary TEXT,
            learner_notes_summary TEXT,
            recommended_next_steps JSONB NOT NULL DEFAULT '[]'::jsonb,
            provenance JSONB NOT NULL DEFAULT '{}'::jsonb,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_session_intelligence_session_id ON session_intelligence(session_id);
        CREATE INDEX IF NOT EXISTS idx_session_intelligence_session_status ON session_intelligence(session_id, status);
    """))


def downgrade() -> None:
    op.execute(sa.text("""
        DROP TABLE IF EXISTS session_intelligence CASCADE;
        DROP TABLE IF EXISTS session_action_items CASCADE;
        DROP TABLE IF EXISTS session_topics CASCADE;
        DROP TABLE IF EXISTS session_notes CASCADE;
    """))
