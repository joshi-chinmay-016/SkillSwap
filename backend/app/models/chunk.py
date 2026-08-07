"""
Chunk — SQLAlchemy model for semantic text chunks (Day 68 Part A2).

Relationships:
    ParsedDocument 1 ──── * Chunk

Every chunk belongs to exactly one ParsedDocument and inherits its user_id
for O(1) ownership queries.

Status lifecycle:
    PENDING  → READY     (chunk successfully generated and stored)
    READY    → ARCHIVED  (rechunking: old chunks archived, new READY set replaces them)

Future:
    READY → EMBEDDED   (Day 69: embedding vector generated)
    EMBEDDED → INDEXED (Day 70: stored in vector database)
"""
from __future__ import annotations

import enum
import uuid
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
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


# ── Enums ─────────────────────────────────────────────────────────────────────

class ChunkStatus(str, enum.Enum):
    """
    Lifecycle status of a persisted chunk.

    PENDING   — chunk record created but not yet fully validated.
    READY     — chunk is valid and available for embedding generation.
    ARCHIVED  — superseded by a newer chunk set (rechunking).

    Future (do NOT add yet):
        EMBEDDED — embedding vector has been generated (Day 69).
        INDEXED  — stored in vector database (Day 70).
    """

    PENDING = "PENDING"
    READY = "READY"
    ARCHIVED = "ARCHIVED"


# ── Model ─────────────────────────────────────────────────────────────────────

class Chunk(Base):
    """
    One semantic text chunk extracted from a ParsedDocument.

    Chunks are the canonical input for embedding generation (Day 69+).
    They must never be modified after reaching READY status — rechunking
    produces a new set and archives the old one.

    Security notes:
        - user_id is denormalised for O(1) ownership validation.
        - chunk_text is stored in full; never truncated.
        - section/page metadata is optional and sourced from the parser.
    """

    __tablename__ = "chunks"

    # ── Identity ──────────────────────────────────────────────────────────────

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        comment="UUID v4 — unique chunk identifier.",
    )

    # ── Ownership ─────────────────────────────────────────────────────────────

    parsed_document_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("parsed_documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Parent ParsedDocument. CASCADE delete removes chunks when doc is deleted.",
    )

    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Denormalised owner user_id for O(1) ownership queries.",
    )

    # ── Position ──────────────────────────────────────────────────────────────

    chunk_index: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Zero-based reading-order position within the parsed document.",
    )

    # ── Content ───────────────────────────────────────────────────────────────

    chunk_text: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Full text content of this chunk.",
    )

    # ── Offsets ───────────────────────────────────────────────────────────────

    start_offset: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="Character offset (inclusive) into ParsedDocument.text_content.",
    )

    end_offset: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="Character offset (exclusive) into ParsedDocument.text_content.",
    )

    # ── Token Metadata ────────────────────────────────────────────────────────

    estimated_tokens: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="Approximate token count (chars / 4). No tokenizer required.",
    )

    # ── Chunk Configuration ───────────────────────────────────────────────────

    chunk_size: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=800,
        comment="chunk_size setting used when this chunk was generated.",
    )

    overlap_size: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=150,
        comment="chunk_overlap setting used when this chunk was generated.",
    )

    # ── Source Mapping ────────────────────────────────────────────────────────

    page_start: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="First page this chunk spans (if parser provides page info).",
    )

    page_end: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="Last page this chunk spans (if parser provides page info).",
    )

    section: Mapped[Optional[str]] = mapped_column(
        String(512),
        nullable=True,
        comment="Section/heading label this chunk falls under.",
    )

    # ── Strategy Metadata ─────────────────────────────────────────────────────

    strategy: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        default="recursive",
        comment="Name of the chunking strategy that produced this chunk.",
    )

    strategy_version: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="1.0.0",
        comment="Semantic version of the chunking strategy.",
    )

    # ── Status ────────────────────────────────────────────────────────────────

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=ChunkStatus.PENDING.value,
        comment="Chunk lifecycle status.",
    )

    # ── Timestamps ────────────────────────────────────────────────────────────

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=sa.func.now(),
        nullable=False,
        comment="When this chunk was persisted.",
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=sa.func.now(),
        onupdate=sa.func.now(),
        nullable=False,
        comment="Last status update.",
    )

    # ── Future embedding fields (prepared, NOT populated yet) ─────────────────
    # embedding_status: str   — Day 69
    # embedding_model: str    — Day 69
    # embedding_version: str  — Day 69
    # vector_id: str          — Day 70

    # ── Relationships ─────────────────────────────────────────────────────────

    parsed_document = relationship(
        "ParsedDocument",
        back_populates="chunks",
    )

    user = relationship(
        "User",
        foreign_keys=[user_id],
    )

    # ── Indexes ───────────────────────────────────────────────────────────────

    __table_args__ = (
        Index("idx_chunk_parsed_document_id", "parsed_document_id"),
        Index("idx_chunk_user_id", "user_id"),
        Index("idx_chunk_status", "status"),
        Index("idx_chunk_parsed_doc_status", "parsed_document_id", "status"),
        Index("idx_chunk_parsed_doc_index", "parsed_document_id", "chunk_index"),
        Index("idx_chunk_user_status", "user_id", "status"),
    )

    def __repr__(self) -> str:
        return (
            f"<Chunk id={self.id!r} parsed_document_id={self.parsed_document_id!r} "
            f"index={self.chunk_index} status={self.status!r} "
            f"chars={len(self.chunk_text or '')}>"
        )
