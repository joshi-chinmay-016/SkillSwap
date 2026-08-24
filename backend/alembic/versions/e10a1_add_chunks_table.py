"""add chunks table

Revision ID: e10a1_add_chunks_table
Revises: d90a1_add_documents_and_parsed_documents
Create Date: 2026-08-07 22:00:00.000000

Day 68 Part A2 — Chunk Storage & Management Layer.

Creates the `chunks` table with:
    - Full source mapping (offsets, page, section)
    - Strategy metadata (name, version)
    - Lifecycle status (PENDING / READY / ARCHIVED)
    - Denormalised user_id for O(1) ownership queries
    - Composite indexes optimised for Day 69+ embedding queries
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers
revision: str = "e10a1_add_chunks_table"
down_revision: Union[str, None] = "d90a1_docs_and_parsed_docs"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "chunks",
        # ── Identity ──────────────────────────────────────────────────────────
        sa.Column("id", sa.String(length=36), nullable=False),

        # ── Ownership ─────────────────────────────────────────────────────────
        sa.Column("parsed_document_id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),

        # ── Position ──────────────────────────────────────────────────────────
        sa.Column("chunk_index", sa.Integer(), nullable=False),

        # ── Content ───────────────────────────────────────────────────────────
        sa.Column("chunk_text", sa.Text(), nullable=False),

        # ── Offsets ───────────────────────────────────────────────────────────
        sa.Column("start_offset", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("end_offset", sa.Integer(), nullable=False, server_default="0"),

        # ── Token Metadata ────────────────────────────────────────────────────
        sa.Column("estimated_tokens", sa.Integer(), nullable=False, server_default="0"),

        # ── Chunk Configuration ───────────────────────────────────────────────
        sa.Column("chunk_size", sa.Integer(), nullable=False, server_default="800"),
        sa.Column("overlap_size", sa.Integer(), nullable=False, server_default="150"),

        # ── Source Mapping ────────────────────────────────────────────────────
        sa.Column("page_start", sa.Integer(), nullable=True),
        sa.Column("page_end", sa.Integer(), nullable=True),
        sa.Column("section", sa.String(length=512), nullable=True),

        # ── Strategy Metadata ─────────────────────────────────────────────────
        sa.Column("strategy", sa.String(length=64), nullable=False, server_default="recursive"),
        sa.Column("strategy_version", sa.String(length=32), nullable=False, server_default="1.0.0"),

        # ── Status ────────────────────────────────────────────────────────────
        sa.Column("status", sa.String(length=20), nullable=False, server_default="PENDING"),

        # ── Timestamps ────────────────────────────────────────────────────────
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),

        # ── Constraints ───────────────────────────────────────────────────────
        sa.ForeignKeyConstraint(
            ["parsed_document_id"],
            ["parsed_documents.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # ── Indexes ───────────────────────────────────────────────────────────────
    op.create_index("idx_chunk_parsed_document_id", "chunks", ["parsed_document_id"])
    op.create_index("idx_chunk_user_id", "chunks", ["user_id"])
    op.create_index("idx_chunk_status", "chunks", ["status"])
    op.create_index(
        "idx_chunk_parsed_doc_status", "chunks", ["parsed_document_id", "status"]
    )
    op.create_index(
        "idx_chunk_parsed_doc_index", "chunks", ["parsed_document_id", "chunk_index"]
    )
    op.create_index("idx_chunk_user_status", "chunks", ["user_id", "status"])


def downgrade() -> None:
    op.drop_index("idx_chunk_user_status", table_name="chunks")
    op.drop_index("idx_chunk_parsed_doc_index", table_name="chunks")
    op.drop_index("idx_chunk_parsed_doc_status", table_name="chunks")
    op.drop_index("idx_chunk_status", table_name="chunks")
    op.drop_index("idx_chunk_user_id", table_name="chunks")
    op.drop_index("idx_chunk_parsed_document_id", table_name="chunks")
    op.drop_table("chunks")
