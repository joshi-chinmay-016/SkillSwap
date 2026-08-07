"""
chunk_generation_job — Background chunk generation runner (Day 68 Part A2).

This module provides a background-task-compatible function that runs the full
chunk generation pipeline in a fresh database session, following the same
pattern as the document parsing retry job in document_router.py.

Usage (FastAPI BackgroundTasks)::

    background_tasks.add_task(
        run_chunk_generation_job,
        document_id=doc.id,
        user_id=current_user.id,
    )

The job handles its own session lifecycle.  Callers do NOT pass a db session.

Retry behaviour:
    Use run_rechunk_job() to archive the previous chunk set and generate a
    fresh one (rechunking without reparsing).
"""
from __future__ import annotations

import logging

from app.core.database import SessionLocal
from app.services.chunk_service import ChunkService

logger = logging.getLogger(__name__)


def run_chunk_generation_job(
    *,
    document_id: str,
    user_id: int,
    chunk_size: int | None = None,
    chunk_overlap: int | None = None,
    strategy_name: str | None = None,
) -> None:
    """
    Background job: generate and persist chunks for a parsed document.

    Opens its own database session and closes it in a `finally` block,
    mirroring the pattern used in document_router.py's ``_run_retry()``.

    Args:
        document_id   : UUID of the parent Document.
        user_id       : Authenticated owner's user ID.
        chunk_size    : Optional override for chunk size (chars).
        chunk_overlap : Optional override for overlap (chars).
        strategy_name : Optional strategy name override.

    Logs:
        - Job started (with document_id, user_id).
        - Chunk count and strategy on success.
        - Full exception traceback on failure.
    """
    logger.info(
        "chunk_generation_job — started for document_id=%s user_id=%d",
        document_id,
        user_id,
    )

    db = SessionLocal()
    try:
        result = ChunkService.save_chunks(
            db,
            document_id=document_id,
            user_id=user_id,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            strategy_name=strategy_name,
        )
        logger.info(
            "chunk_generation_job — completed: %d chunks (strategy=%s v%s) "
            "for document_id=%s",
            result.chunk_count,
            result.strategy,
            result.strategy_version,
            document_id,
        )
    except Exception as exc:
        logger.exception(
            "chunk_generation_job — failed for document_id=%s: %s",
            document_id,
            exc,
        )
    finally:
        db.close()


def run_rechunk_job(
    *,
    document_id: str,
    user_id: int,
    chunk_size: int | None = None,
    chunk_overlap: int | None = None,
    strategy_name: str | None = None,
) -> None:
    """
    Background job: archive existing chunks and regenerate for a document.

    Rechunking flow:
        1. Archive all READY chunks → ARCHIVED.
        2. Generate fresh chunks using the configured (or overridden) strategy.
        3. Persist new READY chunk set.

    This allows re-chunking after a strategy update without reparsing.

    Args:
        document_id   : UUID of the parent Document.
        user_id       : Authenticated owner's user ID.
        chunk_size    : Optional override for chunk size (chars).
        chunk_overlap : Optional override for overlap (chars).
        strategy_name : Optional strategy name override.
    """
    logger.info(
        "rechunk_job — started for document_id=%s user_id=%d",
        document_id,
        user_id,
    )

    db = SessionLocal()
    try:
        result = ChunkService.regenerate_chunks(
            db,
            document_id=document_id,
            user_id=user_id,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            strategy_name=strategy_name,
        )
        logger.info(
            "rechunk_job — completed: %d chunks (strategy=%s v%s) for document_id=%s. %s",
            result.chunk_count,
            result.strategy,
            result.strategy_version,
            document_id,
            result.message,
        )
    except Exception as exc:
        logger.exception(
            "rechunk_job — failed for document_id=%s: %s",
            document_id,
            exc,
        )
    finally:
        db.close()
