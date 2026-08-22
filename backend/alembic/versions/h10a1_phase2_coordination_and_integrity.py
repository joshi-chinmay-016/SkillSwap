"""add phase 2 session coordination, meeting_room_id, and indexes

Revision ID: h10a1_phase2_coord
Revises: g10a1_booking_avail
Create Date: 2026-08-21 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'h10a1_phase2_coord'
down_revision = 'g10a1_booking_avail'
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    # 1. Update sessions table
    if 'sessions' in inspector.get_table_names():
        session_cols = [c['name'] for c in inspector.get_columns('sessions')]
        if 'meeting_room_id' not in session_cols:
            op.add_column(
                'sessions',
                sa.Column('meeting_room_id', sa.String(length=100), nullable=True)
            )

        existing_indexes = [idx['name'] for idx in inspector.get_indexes('sessions')]
        if 'idx_sessions_mentor_active_range' not in existing_indexes:
            try:
                op.create_index(
                    'idx_sessions_mentor_active_range',
                    'sessions',
                    ['mentor_id', 'status', 'scheduled_at'],
                    unique=False
                )
            except Exception:
                pass

        if 'idx_sessions_requester_active_range' not in existing_indexes:
            try:
                op.create_index(
                    'idx_sessions_requester_active_range',
                    'sessions',
                    ['requester_id', 'status', 'scheduled_at'],
                    unique=False
                )
            except Exception:
                pass


def downgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    if 'sessions' in inspector.get_table_names():
        existing_indexes = [idx['name'] for idx in inspector.get_indexes('sessions')]
        if 'idx_sessions_mentor_active_range' in existing_indexes:
            op.drop_index('idx_sessions_mentor_active_range', table_name='sessions')
        if 'idx_sessions_requester_active_range' in existing_indexes:
            op.drop_index('idx_sessions_requester_active_range', table_name='sessions')

        session_cols = [c['name'] for c in inspector.get_columns('sessions')]
        if 'meeting_room_id' in session_cols:
            op.drop_column('sessions', 'meeting_room_id')
