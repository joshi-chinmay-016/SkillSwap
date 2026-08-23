"""create oauth_identities table for Phase 7 OAuth authentication

Revision ID: l10a2_phase7_oauth_identities
Revises: l10a1_phase5_session_realtime
Create Date: 2026-08-23 22:40:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'l10a2_phase7_oauth_identities'
down_revision = 'l10a1_phase5_session_realtime'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'oauth_identities',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('provider', sa.String(length=50), nullable=False),
        sa.Column('provider_user_id', sa.String(length=255), nullable=False),
        sa.Column('provider_email', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.UniqueConstraint('provider', 'provider_user_id', name='uq_provider_user')
    )
    op.create_index('ix_oauth_identities_user_id', 'oauth_identities', ['user_id'], unique=False)
    op.create_index('ix_oauth_identities_provider_user', 'oauth_identities', ['provider', 'provider_user_id'], unique=True)


def downgrade() -> None:
    op.drop_index('ix_oauth_identities_provider_user', table_name='oauth_identities')
    op.drop_index('ix_oauth_identities_user_id', table_name='oauth_identities')
    op.drop_table('oauth_identities')
