"""create role and is_active columns on users, create admin_audit_logs and reports tables for Phase 8

Revision ID: m10a1_phase8_rbac_and_admin
Revises: l10a2_phase7_oauth_identities
Create Date: 2026-08-24 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'm10a1_phase8_rbac_and_admin'
down_revision = 'l10a2_phase7_oauth_identities'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Add role and is_active to users
    op.add_column('users', sa.Column('role', sa.String(length=20), server_default='USER', nullable=False))
    op.add_column('users', sa.Column('is_active', sa.Boolean(), server_default=sa.text('true'), nullable=False))
    op.create_index('ix_users_role', 'users', ['role'], unique=False)
    op.create_index('ix_users_is_active', 'users', ['is_active'], unique=False)

    # 2. Create admin_audit_logs table
    op.create_table(
        'admin_audit_logs',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('admin_user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('action', sa.String(length=100), nullable=False),
        sa.Column('target_type', sa.String(length=50), nullable=False),
        sa.Column('target_id', sa.String(length=100), nullable=True),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('metadata_json', sa.Text(), nullable=True),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )
    op.create_index('ix_admin_audit_logs_action', 'admin_audit_logs', ['action'], unique=False)
    op.create_index('ix_admin_audit_logs_admin_user_id', 'admin_audit_logs', ['admin_user_id'], unique=False)
    op.create_index('ix_admin_audit_logs_created_at', 'admin_audit_logs', ['created_at'], unique=False)
    op.create_index('ix_admin_audit_logs_target', 'admin_audit_logs', ['target_type', 'target_id'], unique=False)

    # 3. Create reports table
    op.create_table(
        'reports',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('reporter_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('reported_user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('session_id', sa.Integer(), sa.ForeignKey('sessions.id', ondelete='SET NULL'), nullable=True),
        sa.Column('reason', sa.Text(), nullable=False),
        sa.Column('status', sa.String(length=20), server_default='OPEN', nullable=False),
        sa.Column('resolution_notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index('ix_reports_status', 'reports', ['status'], unique=False)
    op.create_index('ix_reports_reporter_id', 'reports', ['reporter_id'], unique=False)
    op.create_index('ix_reports_reported_user_id', 'reports', ['reported_user_id'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_reports_reported_user_id', table_name='reports')
    op.drop_index('ix_reports_reporter_id', table_name='reports')
    op.drop_index('ix_reports_status', table_name='reports')
    op.drop_table('reports')

    op.drop_index('ix_admin_audit_logs_target', table_name='admin_audit_logs')
    op.drop_index('ix_admin_audit_logs_created_at', table_name='admin_audit_logs')
    op.drop_index('ix_admin_audit_logs_admin_user_id', table_name='admin_audit_logs')
    op.drop_index('ix_admin_audit_logs_action', table_name='admin_audit_logs')
    op.drop_table('admin_audit_logs')

    op.drop_index('ix_users_is_active', table_name='users')
    op.drop_index('ix_users_role', table_name='users')
    op.drop_column('users', 'is_active')
    op.drop_column('users', 'role')
