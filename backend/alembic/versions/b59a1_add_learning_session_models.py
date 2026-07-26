"""add learning session models

Revision ID: b59a10000001
Revises: a58a10000001
Create Date: 2026-07-27 16:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b59a10000001'
down_revision: Union[str, None] = 'a58a10000001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'learning_sessions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('uuid', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('journey_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('status', sa.String(length=20), server_default='ACTIVE', nullable=False),
        sa.Column('started_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('ended_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['journey_id'], ['learning_journeys.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('uuid')
    )
    op.create_index('ix_learning_sessions_uuid', 'learning_sessions', ['uuid'], unique=True)
    op.create_index('ix_learning_sessions_user_id', 'learning_sessions', ['user_id'], unique=False)
    op.create_index('ix_learning_sessions_journey_id', 'learning_sessions', ['journey_id'], unique=False)
    op.create_index('idx_learning_sessions_user_status', 'learning_sessions', ['user_id', 'status'], unique=False)
    op.create_index('idx_learning_sessions_journey_status', 'learning_sessions', ['journey_id', 'status'], unique=False)
    op.create_index('idx_learning_sessions_user_created', 'learning_sessions', ['user_id', 'created_at'], unique=False)


def downgrade() -> None:
    op.drop_index('idx_learning_sessions_user_created', table_name='learning_sessions')
    op.drop_index('idx_learning_sessions_journey_status', table_name='learning_sessions')
    op.drop_index('idx_learning_sessions_user_status', table_name='learning_sessions')
    op.drop_index('ix_learning_sessions_journey_id', table_name='learning_sessions')
    op.drop_index('ix_learning_sessions_user_id', table_name='learning_sessions')
    op.drop_index('ix_learning_sessions_uuid', table_name='learning_sessions')
    op.drop_table('learning_sessions')
