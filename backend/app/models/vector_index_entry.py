"""
VectorIndexEntry — SQLAlchemy model tracking which embeddings are in FAISS (Day 70).

This table is the PostgreSQL source of truth for:
    - Which embeddings have been indexed in FAISS.
    - The FAISS vector ID (faiss_id) for each indexed embedding.
    - Indexing status (INDEXED | INDEX_FAILED | REMOVED).
    - Crash recovery: what was successfully persisted.

Relationships:
    Embedding 1 ──── 0..1 VectorIndexEntry

Design notes:
    - One row per embedding_id. Unique constraint prevents duplicates.
    - faiss_id is deterministic (SHA-256 of embedding_id) — not a sequence.
    - On CASCADE DELETE of the parent embedding, this entry is removed automatically.
    - The mapping JSON file on disk mirrors this table for FAISS startup loading.
    - PostgreSQL owns metadata; FAISS owns the binary index.
"""
from __future__ import annotations

import enum
from datetime import datetime
from typing import Optional

import sqlalchemy as sa
from sqlalchemy import (
    BigInteger,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


# ── Enum ──────────────────────────────────────────────────────────────────────

class VectorIndexStatus(str, enum.Enum):
    """
    Lifecycle status of a vector index entry.

    INDEXED      — embedding vector is present in the FAISS index on disk.
    INDEX_FAILED — indexing attempted but failed; embedding is eligible for retry.
    REMOVED      — vector was removed from FAISS (e.g., embedding archived).
    """

    INDEXED = "INDEXED"
    INDEX_FAILED = "INDEX_FAILED"
    REMOVED = "REMOVED"


# ── Model ─────────────────────────────────────────────────────────────────────

class VectorIndexEntry(Base):
    """
    Tracks the FAISS indexing status for each embedding.

    One row per embedding. The faiss_id is the int64 vector ID used inside FAISS,
    derived deterministically from the embedding_id UUID.

    Ownership chain: User → Document → ParsedDocument → Chunk → Embedding → VectorIndexEntry
    """

    __tablename__ = "vector_index_entries"

    # ── Identity ──────────────────────────────────────────────────────────────

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
        comment="Auto-increment surrogate primary key.",
    )

    # ── Embedding reference ───────────────────────────────────────────────────

    embedding_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("embeddings.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        comment="Parent Embedding UUID. CASCADE delete removes this entry when embedding is deleted.",
    )

    # ── FAISS vector ID ───────────────────────────────────────────────────────

    faiss_id: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        unique=True,
        comment=(
            "Deterministic int64 FAISS vector ID. "
            "Derived as SHA-256(embedding_id) truncated to 63 bits. "
            "Used for FAISS add_with_ids() and remove_ids()."
        ),
    )

    # ── Status ────────────────────────────────────────────────────────────────

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=VectorIndexStatus.INDEXED.value,
        comment="Vector indexing lifecycle status.",
    )

    # ── Timestamps ────────────────────────────────────────────────────────────

    indexed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=sa.func.now(),
        nullable=False,
        comment="When this vector was successfully added to the FAISS index.",
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=sa.func.now(),
        onupdate=sa.func.now(),
        nullable=False,
        comment="Last status update.",
    )

    # ── Failure information ───────────────────────────────────────────────────

    failure_reason: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Human-readable failure reason when status=INDEX_FAILED.",
    )

    # ── Relationships ─────────────────────────────────────────────────────────

    embedding = relationship(
        "Embedding",
        foreign_keys=[embedding_id],
    )

    # ── Indexes & Constraints ─────────────────────────────────────────────────

    __table_args__ = (
        Index("idx_vector_index_entry_embedding_id", "embedding_id"),
        Index("idx_vector_index_entry_faiss_id", "faiss_id"),
        Index("idx_vector_index_entry_status", "status"),
    )

    def __repr__(self) -> str:
        return (
            f"<VectorIndexEntry id={self.id} embedding_id={self.embedding_id!r} "
            f"faiss_id={self.faiss_id} status={self.status!r}>"
        )
