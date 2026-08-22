"""add specific_date column to mentor_availability

Revision ID: i10a1_mentor_avail_date
Revises: h10a1_phase2_coord
Create Date: 2026-08-21 16:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'i10a1_mentor_avail_date'
down_revision = 'h10a1_phase2_coord'
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    # 1. Update mentor_availability table
    if 'mentor_availability' in inspector.get_table_names():
        avail_cols = [c['name'] for c in inspector.get_columns('mentor_availability')]
        if 'specific_date' not in avail_cols:
            op.add_column(
                'mentor_availability',
                sa.Column('specific_date', sa.Date(), nullable=True)
            )

        existing_indexes = [idx['name'] for idx in inspector.get_indexes('mentor_availability')]
        if 'idx_mentor_avail_date_lookup' not in existing_indexes:
            try:
                op.create_index(
                    'idx_mentor_avail_date_lookup',
                    'mentor_availability',
                    ['mentor_id', 'specific_date', 'is_active'],
                    unique=False
                )
            except Exception:
                pass


def downgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    if 'mentor_availability' in inspector.get_table_names():
        existing_indexes = [idx['name'] for idx in inspector.get_indexes('mentor_availability')]
        if 'idx_mentor_avail_date_lookup' in existing_indexes:
            op.drop_index('idx_mentor_avail_date_lookup', table_name='mentor_availability')

        avail_cols = [c['name'] for c in inspector.get_columns('mentor_availability')]
        if 'specific_date' in avail_cols:
            op.drop_column('mentor_availability', 'specific_date')
