"""
EmbeddingRepository — Persistence functions for Embedding records (Day 69 Part A2).

Follows the same function-based repository convention as chunk_repository.py.

All functions:
    - Accept a SQLAlchemy Session as their first argument.
    - Return ORM objects or None / empty list.
    - Never commit — callers own the transaction.
    - Never contain business logic.
    - Never expose raw vectors in log messages.

Functions:
    create_embedding()
    bulk_create_embeddings()
    get_embedding()
    get_embedding_by_chunk()
    get_active_embedding_by_chunk()
    get_embeddings_by_document()
    exists_for_version()
    update_embedding_status()
    archive_embedding()
    bulk_archive_embeddings()
    count_embeddings_by_document()
    list_ready_embeddings()
    list_failed_embeddings()
    get_chunks_needing_embeddings()
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from app.models.embedding import Embedding, EmbeddingStatus

logger = logging.getLogger(__name__)


# ── Create ─────────────────────────────────────────────────────────────────────

def create_embedding(
    db: Session,
    *,
    chunk_id: str,
    parsed_document_id: str,
    user_id: int,
    provider: str,
    model_name: str,
    model_version: str,
    embedding_version: int,
    dimension: int,
    status: str = EmbeddingStatus.PENDING.value,
    vector: list[float] | None = None,
) -> Embedding:
    """
    Persist a single embedding record.

    Prefer :func:`bulk_create_embeddings` for large documents.
    The vector is optional at creation time — PENDING records have no vector.
    """
    emb = Embedding(
        chunk_id=chunk_id,
        parsed_document_id=parsed_document_id,
        user_id=user_id,
        provider=provider,
        model_name=model_name,
        model_version=model_version,
        embedding_version=embedding_version,
        dimension=dimension,
        status=status,
    )
    if vector is not None:
        emb.set_vector(vector)
    db.add(emb)
    db.flush()
    return emb


def bulk_create_embeddings(
    db: Session,
    *,
    records: list[dict],
) -> list[Embedding]:
    """
    Persist multiple embedding records in a single flush.

    If an embedding record already exists for a (chunk_id, provider, model_name,
    model_version, embedding_version) tuple, its status and metadata are updated
    rather than attempting a duplicate insert.

    Args:
        db      : Active SQLAlchemy session.
        records : List of dicts with keys matching Embedding constructor args.
                  Required keys: chunk_id, parsed_document_id, user_id, provider,
                                 model_name, model_version, embedding_version, dimension.
                  Optional keys: status, vector.

    Returns:
        List of persisted Embedding ORM objects (IDs populated after flush).
    """
    if not records:
        return []

    # Query existing records matching the unique constraint criteria
    chunk_ids = [rec["chunk_id"] for rec in records]
    provider = records[0]["provider"]
    model_name = records[0]["model_name"]
    model_version = records[0]["model_version"]
    embedding_version = records[0]["embedding_version"]

    existing_rows = (
        db.query(Embedding)
        .filter(
            Embedding.chunk_id.in_(chunk_ids),
            Embedding.provider == provider,
            Embedding.model_name == model_name,
            Embedding.model_version == model_version,
            Embedding.embedding_version == embedding_version,
        )
        .all()
    )
    existing_map = {emb.chunk_id: emb for emb in existing_rows}

    embeddings: list[Embedding] = []
    for rec in records:
        chunk_id = rec["chunk_id"]
        if chunk_id in existing_map:
            emb = existing_map[chunk_id]
            emb.status = rec.get("status", EmbeddingStatus.PENDING.value)
            emb.failure_count = 0
            emb.error_category = None
            if rec.get("vector") is not None:
                emb.set_vector(rec["vector"])
        else:
            emb = Embedding(
                chunk_id=rec["chunk_id"],
                parsed_document_id=rec["parsed_document_id"],
                user_id=rec["user_id"],
                provider=rec["provider"],
                model_name=rec["model_name"],
                model_version=rec["model_version"],
                embedding_version=rec["embedding_version"],
                dimension=rec["dimension"],
                status=rec.get("status", EmbeddingStatus.PENDING.value),
            )
            if rec.get("vector") is not None:
                emb.set_vector(rec["vector"])
            db.add(emb)
        embeddings.append(emb)

    db.flush()

    logger.debug(
        "bulk_create_embeddings — upserted %d records for parsed_document_id=%s",
        len(embeddings),
        records[0].get("parsed_document_id", "?") if records else "?",
    )
    return embeddings


# ── Read ───────────────────────────────────────────────────────────────────────

def get_embedding(db: Session, embedding_id: str) -> Optional[Embedding]:
    """Fetch a single embedding by its UUID."""
    return db.query(Embedding).filter(Embedding.id == embedding_id).first()


def get_embedding_by_chunk(
    db: Session,
    chunk_id: str,
) -> list[Embedding]:
    """Return all embeddings for a given chunk, ordered by created_at."""
    return (
        db.query(Embedding)
        .filter(Embedding.chunk_id == chunk_id)
        .order_by(Embedding.created_at)
        .all()
    )


def get_active_embedding_by_chunk(
    db: Session,
    chunk_id: str,
    *,
    provider: str,
    model_name: str,
    model_version: str,
    embedding_version: int,
) -> Optional[Embedding]:
    """
    Return the non-archived embedding for the given chunk/model/version identity.

    Returns None if no active embedding exists (not yet generated, or only FAILED).
    """
    return (
        db.query(Embedding)
        .filter(
            Embedding.chunk_id == chunk_id,
            Embedding.provider == provider,
            Embedding.model_name == model_name,
            Embedding.model_version == model_version,
            Embedding.embedding_version == embedding_version,
            Embedding.status != EmbeddingStatus.ARCHIVED.value,
        )
        .first()
    )


def get_embeddings_by_document(
    db: Session,
    parsed_document_id: str,
    *,
    status_filter: Optional[str] = None,
) -> list[Embedding]:
    """Return all embeddings for a document, optionally filtered by status."""
    q = db.query(Embedding).filter(
        Embedding.parsed_document_id == parsed_document_id
    )
    if status_filter:
        q = q.filter(Embedding.status == status_filter)
    return q.order_by(Embedding.created_at).all()


def exists_for_version(
    db: Session,
    chunk_id: str,
    *,
    provider: str,
    model_name: str,
    model_version: str,
    embedding_version: int,
    ready_only: bool = True,
) -> bool:
    """
    Check whether an active embedding already exists for this chunk/model/version.

    Args:
        db               : Active session.
        chunk_id         : Target chunk UUID.
        provider         : Provider name.
        model_name       : Model identifier.
        model_version    : Provider model version.
        embedding_version: Application embedding version.
        ready_only       : If True, only count READY embeddings (not PENDING/PROCESSING).

    Returns:
        True if a matching embedding exists; False otherwise.
    """
    q = db.query(Embedding).filter(
        Embedding.chunk_id == chunk_id,
        Embedding.provider == provider,
        Embedding.model_name == model_name,
        Embedding.model_version == model_version,
        Embedding.embedding_version == embedding_version,
        Embedding.status != EmbeddingStatus.ARCHIVED.value,
    )
    if ready_only:
        q = q.filter(Embedding.status == EmbeddingStatus.READY.value)
    return db.query(q.exists()).scalar()


# ── Update ─────────────────────────────────────────────────────────────────────

def update_embedding_status(
    db: Session,
    embedding: Embedding,
    status: str,
    *,
    error_category: str | None = None,
    increment_failure: bool = False,
) -> Embedding:
    """
    Update the status of a single embedding record.

    Args:
        db                : Active SQLAlchemy session.
        embedding         : The Embedding ORM object to update.
        status            : New EmbeddingStatus value.
        error_category    : Set when transitioning to FAILED.
        increment_failure : If True, increment failure_count by 1.
    """
    embedding.status = status
    if error_category is not None:
        embedding.error_category = error_category
    if increment_failure:
        embedding.failure_count = (embedding.failure_count or 0) + 1
    db.flush()
    return embedding


def update_embedding_vector(
    db: Session,
    embedding: Embedding,
    vector: list[float],
    *,
    status: str = EmbeddingStatus.READY.value,
) -> Embedding:
    """
    Store the generated vector and mark the embedding as READY (or given status).

    Args:
        db        : Active session.
        embedding : The Embedding ORM object to update.
        vector    : The validated float vector to persist.
        status    : Status to set (default: READY).
    """
    embedding.set_vector(vector)
    embedding.status = status
    db.flush()
    return embedding


# ── Archive ────────────────────────────────────────────────────────────────────

def archive_embedding(
    db: Session,
    embedding: Embedding,
) -> Embedding:
    """
    Transition a single embedding to ARCHIVED status.

    Sets archived_at to the current UTC time.
    """
    embedding.status = EmbeddingStatus.ARCHIVED.value
    embedding.archived_at = datetime.now(timezone.utc)
    db.flush()
    return embedding


def bulk_archive_embeddings(
    db: Session,
    chunk_ids: list[str],
    *,
    provider: str,
    model_name: str,
    model_version: str | None = None,
    from_status: str = EmbeddingStatus.READY.value,
) -> int:
    """
    Archive all matching embeddings for a list of chunk IDs.

    Used when re-embedding with a new model version: old READY embeddings
    are archived before the new set is generated.

    Args:
        db            : Active session.
        chunk_ids     : List of chunk UUIDs to archive.
        provider      : Provider name filter.
        model_name    : Model name filter.
        model_version : Optional model version filter. If None, archives all versions.
        from_status   : Only archive embeddings with this status (default: READY).

    Returns:
        Number of embeddings archived.
    """
    if not chunk_ids:
        return 0

    q = db.query(Embedding).filter(
        Embedding.chunk_id.in_(chunk_ids),
        Embedding.provider == provider,
        Embedding.model_name == model_name,
        Embedding.status == from_status,
    )
    if model_version:
        q = q.filter(Embedding.model_version == model_version)

    embeddings = q.all()
    now = datetime.now(timezone.utc)
    for emb in embeddings:
        emb.status = EmbeddingStatus.ARCHIVED.value
        emb.archived_at = now

    db.flush()

    logger.debug(
        "bulk_archive_embeddings — archived %d embeddings for %d chunks",
        len(embeddings),
        len(chunk_ids),
    )
    return len(embeddings)


# ── Count / List ───────────────────────────────────────────────────────────────

def count_embeddings_by_document(
    db: Session,
    parsed_document_id: str,
    *,
    status_filter: Optional[str] = None,
) -> int:
    """Return the number of embeddings for a document, optionally filtered by status."""
    q = db.query(Embedding).filter(
        Embedding.parsed_document_id == parsed_document_id
    )
    if status_filter:
        q = q.filter(Embedding.status == status_filter)
    return q.count()


def list_ready_embeddings(
    db: Session,
    parsed_document_id: str,
) -> list[Embedding]:
    """Return all READY embeddings for a document."""
    return (
        db.query(Embedding)
        .filter(
            Embedding.parsed_document_id == parsed_document_id,
            Embedding.status == EmbeddingStatus.READY.value,
        )
        .all()
    )


def list_failed_embeddings(
    db: Session,
    parsed_document_id: str,
) -> list[Embedding]:
    """Return all FAILED embeddings for a document (for retry queuing)."""
    return (
        db.query(Embedding)
        .filter(
            Embedding.parsed_document_id == parsed_document_id,
            Embedding.status == EmbeddingStatus.FAILED.value,
        )
        .all()
    )


def get_chunks_without_ready_embedding(
    db: Session,
    parsed_document_id: str,
    *,
    provider: str,
    model_name: str,
    model_version: str,
    embedding_version: int,
) -> list[str]:
    """
    Return chunk_ids that do NOT have a READY embedding for the given model/version.

    Used to support partial completion: only generates embeddings for chunks
    that don't already have a successful embedding.

    Returns:
        List of chunk UUIDs that need (re-)embedding.
    """
    from app.models.chunk import Chunk, ChunkStatus

    # All READY chunk IDs for the document
    ready_chunk_ids = [
        row[0]
        for row in db.query(Chunk.id).filter(
            Chunk.parsed_document_id == parsed_document_id,
            Chunk.status == ChunkStatus.READY.value,
        ).all()
    ]

    if not ready_chunk_ids:
        return []

    # Chunk IDs that already have a READY embedding for this model/version
    embedded_chunk_ids = {
        row[0]
        for row in db.query(Embedding.chunk_id).filter(
            Embedding.parsed_document_id == parsed_document_id,
            Embedding.provider == provider,
            Embedding.model_name == model_name,
            Embedding.model_version == model_version,
            Embedding.embedding_version == embedding_version,
            Embedding.status == EmbeddingStatus.READY.value,
        ).all()
    }

    return [cid for cid in ready_chunk_ids if cid not in embedded_chunk_ids]
