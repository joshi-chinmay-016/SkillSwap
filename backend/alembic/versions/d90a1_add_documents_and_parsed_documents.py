"""add documents and parsed_documents tables

Revision ID: d90a1_add_documents_and_parsed_documents
Revises: d80a1_add_mentor_memories
Create Date: 2026-08-06 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd90a1_docs_and_parsed_docs'
down_revision: Union[str, None] = 'd80a1_add_mentor_memories'

branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. create documents table
    op.create_table(
        'documents',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('original_filename', sa.String(length=512), nullable=False),
        sa.Column('stored_filename', sa.String(length=255), nullable=False),
        sa.Column('display_name', sa.String(length=255), nullable=False),
        sa.Column('file_extension', sa.String(length=10), nullable=False),
        sa.Column('mime_type', sa.String(length=100), nullable=False),
        sa.Column('file_size', sa.BigInteger(), nullable=False),
        sa.Column('storage_path', sa.String(length=1024), nullable=False),
        sa.Column('checksum', sa.String(length=64), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='UPLOADED'),
        sa.Column('uploaded_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_document_user_id', 'documents', ['user_id'], unique=False)
    op.create_index('idx_document_status', 'documents', ['status'], unique=False)
    op.create_index('idx_document_checksum', 'documents', ['checksum'], unique=False)
    op.create_index('idx_document_user_status', 'documents', ['user_id', 'status'], unique=False)
    op.create_index('idx_document_user_uploaded_at', 'documents', ['user_id', 'uploaded_at'], unique=False)
    op.create_index('idx_document_user_checksum', 'documents', ['user_id', 'checksum'], unique=False)

    # 2. create parsed_documents table
    op.create_table(
        'parsed_documents',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('document_id', sa.String(length=36), nullable=False),
        sa.Column('text_content', sa.Text(), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='PENDING'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['document_id'], ['documents.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('document_id')
    )
    op.create_index('idx_parsed_document_document_id', 'parsed_documents', ['document_id'], unique=True)
    op.create_index('idx_parsed_document_status', 'parsed_documents', ['status'], unique=False)


def downgrade() -> None:
    op.drop_index('idx_parsed_document_status', table_name='parsed_documents')
    op.drop_index('idx_parsed_document_document_id', table_name='parsed_documents')
    op.drop_table('parsed_documents')

    op.drop_index('idx_document_user_checksum', table_name='documents')
    op.drop_index('idx_document_user_uploaded_at', table_name='documents')
    op.drop_index('idx_document_user_status', table_name='documents')
    op.drop_index('idx_document_checksum', table_name='documents')
    op.drop_index('idx_document_status', table_name='documents')
    op.drop_index('idx_document_user_id', table_name='documents')
    op.drop_table('documents')
