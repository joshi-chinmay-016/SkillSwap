"""
ChunkRepository — Persistence functions for Chunk records (Day 68 Part A2).

Follows the same function-based repository convention as the rest of the project.

All functions:
    - Accept a SQLAlchemy Session as their first argument.
    - Return ORM objects or None.
    - Never commit — callers own the transaction.
    - Never contain business logic.

Functions:
    create_chunk()
    bulk_create_chunks()
    get_chunk()
    list_chunks_by_document()
    update_chunk_status()
    delete_chunk()
    archive_chunks_for_document()
    get_ready_chunks()
    get_chunk_count()
"""
from __future__ import annotations

import logging
from typing import Optional

from sqlalchemy.orm import Session

from app.models.chunk import Chunk, ChunkStatus
from parsers.chunking.chunk_strategy import ChunkData

logger = logging.getLogger(__name__)


# ── Create ─────────────────────────────────────────────────────────────────────

def create_chunk(
    db: Session,
    *,
    parsed_document_id: str,
    user_id: int,
    chunk_data: ChunkData,
    status: str = ChunkStatus.READY.value,
) -> Chunk:
    """
    Persist a single chunk record.

    Prefer :func:`bulk_create_chunks` for large documents.
    """
    chunk = Chunk(
        parsed_document_id=parsed_document_id,
        user_id=user_id,
        chunk_index=chunk_data.chunk_index,
        chunk_text=chunk_data.chunk_text,
        start_offset=chunk_data.start_offset,
        end_offset=chunk_data.end_offset,
        estimated_tokens=chunk_data.estimated_tokens,
        chunk_size=chunk_data.chunk_size,
        overlap_size=chunk_data.overlap_size,
        page_start=chunk_data.page_start,
        page_end=chunk_data.page_end,
        section=chunk_data.section,
        strategy=chunk_data.strategy,
        strategy_version=chunk_data.strategy_version,
        status=status,
    )
    db.add(chunk)
    db.flush()
    return chunk


def bulk_create_chunks(
    db: Session,
    *,
    parsed_document_id: str,
    user_id: int,
    chunk_data_list: list[ChunkData],
    status: str = ChunkStatus.READY.value,
) -> list[Chunk]:
    """
    Persist multiple chunks in a single flush operation.

    Uses ``db.add_all`` + a single ``db.flush()`` for significantly better
    performance over large documents compared to per-chunk inserts.

    Args:
        db                : Active SQLAlchemy session.
        parsed_document_id: Parent ParsedDocument UUID.
        user_id           : Owner user ID (denormalised).
        chunk_data_list   : ChunkData objects to persist.
        status            : Initial status (default: READY).

    Returns:
        List of persisted Chunk ORM objects (IDs populated after flush).
    """
    if not chunk_data_list:
        return []

    chunks = [
        Chunk(
            parsed_document_id=parsed_document_id,
            user_id=user_id,
            chunk_index=cd.chunk_index,
            chunk_text=cd.chunk_text,
            start_offset=cd.start_offset,
            end_offset=cd.end_offset,
            estimated_tokens=cd.estimated_tokens,
            chunk_size=cd.chunk_size,
            overlap_size=cd.overlap_size,
            page_start=cd.page_start,
            page_end=cd.page_end,
            section=cd.section,
            strategy=cd.strategy,
            strategy_version=cd.strategy_version,
            status=status,
        )
        for cd in chunk_data_list
    ]

    db.add_all(chunks)
    db.flush()

    logger.debug(
        "bulk_create_chunks — inserted %d chunks for parsed_document_id=%s",
        len(chunks),
        parsed_document_id,
    )
    return chunks


# ── Read ───────────────────────────────────────────────────────────────────────

def get_chunk(db: Session, chunk_id: str) -> Optional[Chunk]:
    """Fetch a single chunk by its UUID."""
    return db.query(Chunk).filter(Chunk.id == chunk_id).first()


def list_chunks_by_document(
    db: Session,
    parsed_document_id: str,
    *,
    status_filter: Optional[str] = None,
    page: int = 1,
    page_size: int = 100,
) -> tuple[list[Chunk], int]:
    """
    Return a paginated, ordered list of chunks for a given ParsedDocument.

    Args:
        db                 : Active SQLAlchemy session.
        parsed_document_id : Parent ParsedDocument UUID.
        status_filter      : Optional status to filter by (e.g. 'READY').
        page               : 1-indexed page number.
        page_size          : Records per page.

    Returns:
        Tuple of (chunk list, total count).
    """
    q = (
        db.query(Chunk)
        .filter(Chunk.parsed_document_id == parsed_document_id)
        .order_by(Chunk.chunk_index)
    )

    if status_filter:
        q = q.filter(Chunk.status == status_filter)

    total = q.count()
    chunks = q.offset((page - 1) * page_size).limit(page_size).all()
    return chunks, total


def get_ready_chunks(
    db: Session,
    parsed_document_id: str,
) -> list[Chunk]:
    """Return all READY chunks for a document, ordered by chunk_index."""
    return (
        db.query(Chunk)
        .filter(
            Chunk.parsed_document_id == parsed_document_id,
            Chunk.status == ChunkStatus.READY.value,
        )
        .order_by(Chunk.chunk_index)
        .all()
    )


def get_chunk_count(
    db: Session,
    parsed_document_id: str,
    *,
    status_filter: Optional[str] = None,
) -> int:
    """Return the number of chunks for a document, optionally filtered by status."""
    q = db.query(Chunk).filter(Chunk.parsed_document_id == parsed_document_id)
    if status_filter:
        q = q.filter(Chunk.status == status_filter)
    return q.count()


# ── Update ─────────────────────────────────────────────────────────────────────

def update_chunk_status(
    db: Session,
    chunk: Chunk,
    status: str,
) -> Chunk:
    """Update the status of a single chunk."""
    chunk.status = status
    db.flush()
    return chunk


# ── Delete ─────────────────────────────────────────────────────────────────────

def delete_chunk(db: Session, chunk: Chunk) -> None:
    """Hard-delete a single chunk record."""
    db.delete(chunk)
    db.flush()


# ── Archive ────────────────────────────────────────────────────────────────────

def archive_chunks_for_document(
    db: Session,
    parsed_document_id: str,
    *,
    from_status: str = ChunkStatus.READY.value,
) -> int:
    """
    Transition all chunks for a document from `from_status` to ARCHIVED.

    Used by rechunking flow:
        READY → ARCHIVED  (old set archived before new set is created)

    Args:
        db                 : Active SQLAlchemy session.
        parsed_document_id : Parent ParsedDocument UUID.
        from_status        : Status to archive (default: READY).

    Returns:
        Number of chunks archived.
    """
    updated = (
        db.query(Chunk)
        .filter(
            Chunk.parsed_document_id == parsed_document_id,
            Chunk.status == from_status,
        )
        .all()
    )

    for chunk in updated:
        chunk.status = ChunkStatus.ARCHIVED.value

    db.flush()

    logger.debug(
        "archive_chunks_for_document — archived %d chunks for parsed_document_id=%s",
        len(updated),
        parsed_document_id,
    )
    return len(updated)
