"""
VectorIndexRepository — Persistence functions for VectorIndexEntry records (Day 70).

Follows the same function-based repository convention as embedding_repository.py.

All functions:
    - Accept a SQLAlchemy Session as their first argument.
    - Return ORM objects or None / empty list.
    - Never commit — callers own the transaction.
    - Never contain business logic.
    - Never log raw vector data.

Functions:
    upsert_index_entry()
    get_by_embedding_id()
    get_all_indexed()
    get_indexed_embedding_ids_set()
    list_unindexed_ready_embeddings()
    mark_indexed()
    mark_failed()
    mark_removed()
    bulk_mark_removed()
    count_by_status()
    delete_entry()
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from app.models.embedding import Embedding, EmbeddingStatus
from app.models.vector_index_entry import VectorIndexEntry, VectorIndexStatus

logger = logging.getLogger(__name__)


# ── Create / Upsert ────────────────────────────────────────────────────────────

def upsert_index_entry(
    db: Session,
    *,
    embedding_id: str,
    faiss_id: int,
    status: str = VectorIndexStatus.INDEXED.value,
    failure_reason: str | None = None,
) -> VectorIndexEntry:
    """
    Insert or update a VectorIndexEntry for the given embedding_id.

    If an entry already exists, its status, faiss_id, and failure_reason are updated.
    If no entry exists, a new one is created.

    Args:
        db             : Active SQLAlchemy session.
        embedding_id   : Parent embedding UUID string.
        faiss_id       : FAISS int64 vector ID.
        status         : VectorIndexStatus value (default: INDEXED).
        failure_reason : Human-readable failure description (for INDEX_FAILED status).

    Returns:
        The persisted VectorIndexEntry ORM object.
    """
    entry = get_by_embedding_id(db, embedding_id)
    if entry is None:
        entry = VectorIndexEntry(
            embedding_id=embedding_id,
            faiss_id=faiss_id,
            status=status,
            failure_reason=failure_reason,
        )
        db.add(entry)
    else:
        entry.faiss_id = faiss_id
        entry.status = status
        entry.failure_reason = failure_reason
        entry.updated_at = datetime.now(timezone.utc)

    db.flush()
    return entry


# ── Read ────────────────────────────────────────────────────────────────────────

def get_by_embedding_id(
    db: Session,
    embedding_id: str,
) -> Optional[VectorIndexEntry]:
    """Fetch a VectorIndexEntry by its embedding_id, or None if not found."""
    return (
        db.query(VectorIndexEntry)
        .filter(VectorIndexEntry.embedding_id == embedding_id)
        .first()
    )


def get_all_indexed(db: Session) -> list[VectorIndexEntry]:
    """Return all entries with status INDEXED."""
    return (
        db.query(VectorIndexEntry)
        .filter(VectorIndexEntry.status == VectorIndexStatus.INDEXED.value)
        .all()
    )


def get_indexed_embedding_ids_set(db: Session) -> set[str]:
    """
    Return the set of embedding_ids that have status INDEXED.

    Used for idempotency checking before a batch indexing run.
    More efficient than fetching full ORM objects when only IDs are needed.
    """
    rows = (
        db.query(VectorIndexEntry.embedding_id)
        .filter(VectorIndexEntry.status == VectorIndexStatus.INDEXED.value)
        .all()
    )
    return {row[0] for row in rows}


def list_unindexed_ready_embeddings(
    db: Session,
    *,
    limit: int | None = None,
    parsed_document_id: str | None = None,
    user_id: int | None = None,
) -> list[Embedding]:
    """
    Return READY embeddings that do NOT have a corresponding INDEXED entry.

    These are the candidates for the next indexing batch.

    Args:
        db                 : Active SQLAlchemy session.
        limit              : Maximum number of embeddings to return (None = all).
        parsed_document_id : Restrict to embeddings for a specific document.
        user_id            : Restrict to embeddings owned by a specific user.

    Returns:
        List of Embedding ORM objects eligible for vector indexing.
    """
    from sqlalchemy import select

    # Subquery: embedding_ids that are already INDEXED
    indexed_stmt = select(VectorIndexEntry.embedding_id).where(
        VectorIndexEntry.status == VectorIndexStatus.INDEXED.value
    )

    q = (
        db.query(Embedding)
        .filter(
            Embedding.status == EmbeddingStatus.READY.value,
            Embedding.id.notin_(indexed_stmt),
        )
    )

    if parsed_document_id is not None:
        q = q.filter(Embedding.parsed_document_id == parsed_document_id)

    if user_id is not None:
        q = q.filter(Embedding.user_id == user_id)

    # Order by created_at for deterministic batching
    q = q.order_by(Embedding.created_at)

    if limit is not None:
        q = q.limit(limit)

    return q.all()


def get_all_indexed_faiss_ids(db: Session) -> list[int]:
    """
    Return all faiss_ids that are currently INDEXED.

    Used during reconciliation to compare PostgreSQL against FAISS.
    """
    rows = (
        db.query(VectorIndexEntry.faiss_id)
        .filter(VectorIndexEntry.status == VectorIndexStatus.INDEXED.value)
        .all()
    )
    return [row[0] for row in rows]


def get_indexed_entries_for_document(
    db: Session,
    parsed_document_id: str,
) -> list[VectorIndexEntry]:
    """
    Return all INDEXED VectorIndexEntries for a given document.

    Used for document-level vector removal (archiving, reprocessing).
    """
    return (
        db.query(VectorIndexEntry)
        .join(Embedding, VectorIndexEntry.embedding_id == Embedding.id)
        .filter(
            Embedding.parsed_document_id == parsed_document_id,
            VectorIndexEntry.status == VectorIndexStatus.INDEXED.value,
        )
        .all()
    )


# ── Update ──────────────────────────────────────────────────────────────────────

def mark_indexed(
    db: Session,
    entry: VectorIndexEntry,
    faiss_id: int,
) -> VectorIndexEntry:
    """Transition a VectorIndexEntry to INDEXED status."""
    entry.status = VectorIndexStatus.INDEXED.value
    entry.faiss_id = faiss_id
    entry.failure_reason = None
    entry.updated_at = datetime.now(timezone.utc)
    db.flush()
    return entry


def mark_failed(
    db: Session,
    entry: VectorIndexEntry,
    *,
    failure_reason: str,
) -> VectorIndexEntry:
    """Transition a VectorIndexEntry to INDEX_FAILED status."""
    entry.status = VectorIndexStatus.INDEX_FAILED.value
    entry.failure_reason = failure_reason
    entry.updated_at = datetime.now(timezone.utc)
    db.flush()
    return entry


def mark_removed(
    db: Session,
    entry: VectorIndexEntry,
) -> VectorIndexEntry:
    """Transition a VectorIndexEntry to REMOVED status."""
    entry.status = VectorIndexStatus.REMOVED.value
    entry.updated_at = datetime.now(timezone.utc)
    db.flush()
    return entry


def bulk_mark_removed(
    db: Session,
    embedding_ids: list[str],
) -> int:
    """
    Mark multiple VectorIndexEntries as REMOVED in a single query.

    Args:
        db            : Active SQLAlchemy session.
        embedding_ids : List of embedding UUID strings to mark as REMOVED.

    Returns:
        Number of entries actually updated.
    """
    if not embedding_ids:
        return 0

    entries = (
        db.query(VectorIndexEntry)
        .filter(
            VectorIndexEntry.embedding_id.in_(embedding_ids),
            VectorIndexEntry.status == VectorIndexStatus.INDEXED.value,
        )
        .all()
    )
    now = datetime.now(timezone.utc)
    for entry in entries:
        entry.status = VectorIndexStatus.REMOVED.value
        entry.updated_at = now

    db.flush()
    logger.debug(
        "vector_index_repository.bulk_mark_removed — marked %d entries as REMOVED",
        len(entries),
    )
    return len(entries)


# ── Count ───────────────────────────────────────────────────────────────────────

def count_by_status(db: Session, status: str) -> int:
    """Return the number of VectorIndexEntries with the given status."""
    return (
        db.query(VectorIndexEntry)
        .filter(VectorIndexEntry.status == status)
        .count()
    )


# ── Delete ──────────────────────────────────────────────────────────────────────

def delete_entry(db: Session, embedding_id: str) -> bool:
    """
    Hard-delete a VectorIndexEntry by embedding_id.

    Returns True if an entry was deleted, False if not found.
    """
    entry = get_by_embedding_id(db, embedding_id)
    if entry is None:
        return False
    db.delete(entry)
    db.flush()
    return True
