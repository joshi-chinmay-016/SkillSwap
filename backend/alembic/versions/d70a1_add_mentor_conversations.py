"""add mentor_conversations and mentor_messages tables

Revision ID: d70a1_add_mentor_conversations
Revises: c60a1_add_session_summaries
Create Date: 2026-07-31 20:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd70a1_add_mentor_conversations'
down_revision: Union[str, None] = '0e912b0154ce'

branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── mentor_conversations ──────────────────────────────────────────────────
    op.create_table(
        'mentor_conversations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('journey_id', sa.Integer(), nullable=True),
        sa.Column('session_id', sa.Integer(), nullable=True),
        sa.Column('title', sa.String(length=255), nullable=False, server_default='New Conversation'),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='ACTIVE'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('last_message_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['journey_id'], ['learning_journeys.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['session_id'], ['learning_sessions.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_mentor_conv_user_id', 'mentor_conversations', ['user_id'], unique=False)
    op.create_index('idx_mentor_conv_status', 'mentor_conversations', ['status'], unique=False)
    op.create_index('idx_mentor_conv_last_msg', 'mentor_conversations', ['last_message_at'], unique=False)
    op.create_index('idx_mentor_conv_created', 'mentor_conversations', ['created_at'], unique=False)
    op.create_index('idx_mentor_conv_user_last_msg', 'mentor_conversations', ['user_id', 'last_message_at'], unique=False)

    # ── mentor_messages ───────────────────────────────────────────────────────
    op.create_table(
        'mentor_messages',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('conversation_id', sa.Integer(), nullable=False),
        sa.Column('role', sa.String(length=20), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['conversation_id'], ['mentor_conversations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_mentor_msg_conversation_id', 'mentor_messages', ['conversation_id'], unique=False)
    op.create_index('idx_mentor_msg_created_at', 'mentor_messages', ['created_at'], unique=False)
    op.create_index('idx_mentor_msg_conv_created', 'mentor_messages', ['conversation_id', 'created_at'], unique=False)


def downgrade() -> None:
    op.drop_index('idx_mentor_msg_conv_created', table_name='mentor_messages')
    op.drop_index('idx_mentor_msg_created_at', table_name='mentor_messages')
    op.drop_index('idx_mentor_msg_conversation_id', table_name='mentor_messages')
    op.drop_table('mentor_messages')

    op.drop_index('idx_mentor_conv_user_last_msg', table_name='mentor_conversations')
    op.drop_index('idx_mentor_conv_created', table_name='mentor_conversations')
    op.drop_index('idx_mentor_conv_last_msg', table_name='mentor_conversations')
    op.drop_index('idx_mentor_conv_status', table_name='mentor_conversations')
    op.drop_index('idx_mentor_conv_user_id', table_name='mentor_conversations')
    op.drop_table('mentor_conversations')
