"""reconcile_feedback_session_fk

Revision ID: f70a1_reconcile_feedback_fk
Revises: e5f57eb3748e_create_feedback_table
Create Date: 2026-08-18 22:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f70a1_reconcile_feedback_fk'
down_revision = 'e5f57eb3748e_create_feedback_table'
branch_labels = None
depends_on = None


def upgrade():
    # Update Feedback.session_id Foreign Key from sessions.id to learning_sessions.id
    try:
        op.drop_constraint('feedback_session_id_fkey', 'feedback', type_='foreignkey')
    except Exception:
        pass
    
    op.create_foreign_key(
        'feedback_session_id_fkey',
        'feedback',
        'learning_sessions',
        ['session_id'],
        ['id'],
        ondelete='CASCADE'
    )


def downgrade():
    try:
        op.drop_constraint('feedback_session_id_fkey', 'feedback', type_='foreignkey')
    except Exception:
        pass

    op.create_foreign_key(
        'feedback_session_id_fkey',
        'feedback',
        'sessions',
        ['session_id'],
        ['id']
    )
