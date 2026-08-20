"""add booking and availability infrastructure

Revision ID: g10a1_booking_availability_infrastructure
Revises: f12a1_wallet_welcome_bonus
Create Date: 2026-08-20 23:10:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'g10a1_booking_avail'
down_revision = 'f12a1_wallet_welcome_bonus'
branch_labels = None
depends_on = None



def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    # 1. Update mentor_availability table
    if 'mentor_availability' in inspector.get_table_names():
        avail_cols = [c['name'] for c in inspector.get_columns('mentor_availability')]
        if 'timezone' not in avail_cols:
            op.add_column(
                'mentor_availability',
                sa.Column('timezone', sa.String(length=50), nullable=False, server_default='UTC')
            )
        if 'is_active' not in avail_cols:
            op.add_column(
                'mentor_availability',
                sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true' if conn.dialect.name == 'postgresql' else '1'))
            )
        if 'created_at' not in avail_cols:
            op.add_column(
                'mentor_availability',
                sa.Column('created_at', sa.DateTime(timezone=True), nullable=True, server_default=sa.text('CURRENT_TIMESTAMP'))
            )
        if 'updated_at' not in avail_cols:
            op.add_column(
                'mentor_availability',
                sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True, server_default=sa.text('CURRENT_TIMESTAMP'))
            )

    # 2. Update sessions table
    if 'sessions' in inspector.get_table_names():
        session_cols = [c['name'] for c in inspector.get_columns('sessions')]
        if 'duration_minutes' not in session_cols:
            op.add_column(
                'sessions',
                sa.Column('duration_minutes', sa.Integer(), nullable=False, server_default='60')
            )
        if 'created_at' not in session_cols:
            op.add_column(
                'sessions',
                sa.Column('created_at', sa.DateTime(timezone=True), nullable=True, server_default=sa.text('CURRENT_TIMESTAMP'))
            )
        if 'updated_at' not in session_cols:
            op.add_column(
                'sessions',
                sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True, server_default=sa.text('CURRENT_TIMESTAMP'))
            )

    # 3. Update notifications table
    if 'notifications' in inspector.get_table_names():
        notif_cols = [c['name'] for c in inspector.get_columns('notifications')]
        if 'type' not in notif_cols:
            op.add_column(
                'notifications',
                sa.Column('type', sa.String(length=50), nullable=False, server_default='GENERAL')
            )
        if 'title' not in notif_cols:
            op.add_column(
                'notifications',
                sa.Column('title', sa.String(length=150), nullable=True)
            )
        if 'related_session_id' not in notif_cols:
            op.add_column(
                'notifications',
                sa.Column('related_session_id', sa.Integer(), nullable=True)
            )
        if 'created_at' not in notif_cols:
            op.add_column(
                'notifications',
                sa.Column('created_at', sa.DateTime(timezone=True), nullable=True, server_default=sa.text('CURRENT_TIMESTAMP'))
            )


def downgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    if 'notifications' in inspector.get_table_names():
        notif_cols = [c['name'] for c in inspector.get_columns('notifications')]
        for col in ['created_at', 'related_session_id', 'title', 'type']:
            if col in notif_cols:
                op.drop_column('notifications', col)

    if 'sessions' in inspector.get_table_names():
        session_cols = [c['name'] for c in inspector.get_columns('sessions')]
        for col in ['updated_at', 'created_at', 'duration_minutes']:
            if col in session_cols:
                op.drop_column('sessions', col)

    if 'mentor_availability' in inspector.get_table_names():
        avail_cols = [c['name'] for c in inspector.get_columns('mentor_availability')]
        for col in ['updated_at', 'created_at', 'is_active', 'timezone']:
            if col in avail_cols:
                op.drop_column('mentor_availability', col)
