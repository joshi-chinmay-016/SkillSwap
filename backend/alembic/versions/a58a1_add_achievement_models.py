"""add achievement models

Revision ID: a58a10000001
Revises: ef1c8acdc42d
Create Date: 2026-07-27 15:15:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a58a10000001'
down_revision: Union[str, None] = 'ef1c8acdc42d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('achievements',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.String(length=255), nullable=False),
        sa.Column('category', sa.String(length=50), nullable=False),
        sa.Column('badge_tier', sa.String(length=50), nullable=False),
        sa.Column('badge_name', sa.String(length=100), nullable=False),
        sa.Column('icon', sa.String(length=100), nullable=False),
        sa.Column('requirement_type', sa.String(length=50), nullable=False),
        sa.Column('requirement_value', sa.Integer(), nullable=False),
        sa.Column('xp_reward', sa.Integer(), nullable=False, server_default='50'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default='now()', nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default='now()', nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_achievements_category', 'achievements', ['category'], unique=False)

    op.create_table('user_achievements',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('achievement_id', sa.Integer(), nullable=False),
        sa.Column('unlocked_at', sa.DateTime(timezone=True), server_default='now()', nullable=False),
        sa.ForeignKeyConstraint(['achievement_id'], ['achievements.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'achievement_id', name='uq_user_achievement')
    )
    op.create_index('ix_user_achievements_user_id', 'user_achievements', ['user_id'], unique=False)
    op.create_index('ix_user_achievements_achievement_id', 'user_achievements', ['achievement_id'], unique=False)
    op.create_index('idx_user_achievements_user_ach', 'user_achievements', ['user_id', 'achievement_id'], unique=False)


def downgrade() -> None:
    op.drop_index('idx_user_achievements_user_ach', table_name='user_achievements')
    op.drop_index('ix_user_achievements_achievement_id', table_name='user_achievements')
    op.drop_index('ix_user_achievements_user_id', table_name='user_achievements')
    op.drop_table('user_achievements')
    op.drop_index('ix_achievements_category', table_name='achievements')
    op.drop_table('achievements')
