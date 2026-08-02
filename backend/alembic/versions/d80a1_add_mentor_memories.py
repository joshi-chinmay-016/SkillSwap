"""add mentor_memories table

Revision ID: d80a1_add_mentor_memories
Revises: d70a1_add_mentor_conversations
Create Date: 2026-08-01 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd80a1_add_mentor_memories'
down_revision: Union[str, None] = 'd70a1_add_mentor_conversations'

branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'mentor_memories',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('category', sa.String(length=50), nullable=False, server_default='GENERAL'),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('importance', sa.String(length=20), nullable=False, server_default='MEDIUM'),
        sa.Column('source', sa.String(length=50), nullable=False, server_default='Conversation'),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='ACTIVE'),
        sa.Column('is_pinned', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('last_used_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_memory_user_id', 'mentor_memories', ['user_id'], unique=False)
    op.create_index('idx_memory_category', 'mentor_memories', ['category'], unique=False)
    op.create_index('idx_memory_status', 'mentor_memories', ['status'], unique=False)
    op.create_index('idx_memory_importance', 'mentor_memories', ['importance'], unique=False)
    op.create_index('idx_memory_user_status', 'mentor_memories', ['user_id', 'status'], unique=False)
    op.create_index('idx_memory_user_category', 'mentor_memories', ['user_id', 'category'], unique=False)
    op.create_index('idx_memory_last_used', 'mentor_memories', ['last_used_at'], unique=False)


def downgrade() -> None:
    op.drop_index('idx_memory_last_used', table_name='mentor_memories')
    op.drop_index('idx_memory_user_category', table_name='mentor_memories')
    op.drop_index('idx_memory_user_status', table_name='mentor_memories')
    op.drop_index('idx_memory_importance', table_name='mentor_memories')
    op.drop_index('idx_memory_status', table_name='mentor_memories')
    op.drop_index('idx_memory_category', table_name='mentor_memories')
    op.drop_index('idx_memory_user_id', table_name='mentor_memories')
    op.drop_table('mentor_memories')
