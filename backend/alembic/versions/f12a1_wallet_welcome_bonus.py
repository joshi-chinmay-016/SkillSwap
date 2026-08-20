"""add reference_id and created_at to wallet_transactions

Revision ID: f12a1_wallet_welcome_bonus
Revises: f10a1_skill_verification
Create Date: 2026-08-20 17:25:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'f12a1_wallet_welcome_bonus'
down_revision = 'f10a1_skill_verification'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Check if reference_id column exists before adding
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [c['name'] for c in inspector.get_columns('wallet_transactions')]

    if 'reference_id' not in columns:
        op.add_column(
            'wallet_transactions',
            sa.Column('reference_id', sa.String(length=100), nullable=True)
        )
        op.create_index(
            'ix_wallet_transactions_reference_id',
            'wallet_transactions',
            ['reference_id'],
            unique=True
        )

    if 'created_at' not in columns:
        op.add_column(
            'wallet_transactions',
            sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.text('CURRENT_TIMESTAMP'))
        )


def downgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [c['name'] for c in inspector.get_columns('wallet_transactions')]

    if 'reference_id' in columns:
        op.drop_index('ix_wallet_transactions_reference_id', table_name='wallet_transactions')
        op.drop_column('wallet_transactions', 'reference_id')

    if 'created_at' in columns:
        op.drop_column('wallet_transactions', 'created_at')
