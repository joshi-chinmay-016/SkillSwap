"""
vector_indexing_job — Background job runners for FAISS vector indexing (Day 70).

Provides background-task-compatible functions following the pattern of
embedding_generation_job.py. Each function opens its own database session.

Usage (FastAPI BackgroundTasks)::

    background_tasks.add_task(
        run_vector_indexing_job,
        parsed_document_id=doc.id,
        user_id=current_user.id,
    )

The job handles its own session lifecycle. Callers do NOT pass a db session.
"""
from __future__ import annotations

import logging
import uuid

from app.core.database import SessionLocal
from app.services.vector_indexing_service import VectorIndexingService

logger = logging.getLogger(__name__)


def run_vector_indexing_job(
    *,
    parsed_document_id: str,
    user_id: int,
    job_id: str | None = None,
) -> None:
    """
    Background job: index all READY embeddings for a specific document into FAISS.

    Opens its own database session and closes it in a ``finally`` block.

    Args:
        parsed_document_id : UUID of the ParsedDocument to index.
        user_id            : Authenticated owner's user ID.
        job_id             : Optional operational tracing identifier.
    """
    job_id = job_id or str(uuid.uuid4())
    logger.info(
        "vector_indexing_job — started for parsed_document_id=%s "
        "user_id=%d job_id=%s",
        parsed_document_id,
        user_id,
        job_id,
    )

    db = SessionLocal()
    try:
        service = VectorIndexingService.create()
        result = service.index_document(
            db,
            parsed_document_id=parsed_document_id,
            user_id=user_id,
            job_id=job_id,
        )
        logger.info(
            "vector_indexing_job — completed: "
            "indexed=%d skipped=%d failed=%d index_size=%d "
            "parsed_document_id=%s job_id=%s duration_s=%.3f",
            result.indexed,
            result.skipped,
            result.failed,
            result.index_size,
            parsed_document_id,
            job_id,
            result.duration_s,
        )
    except Exception as exc:
        logger.exception(
            "vector_indexing_job — failed for parsed_document_id=%s job_id=%s: %s",
            parsed_document_id,
            job_id,
            exc,
        )
    finally:
        db.close()


def run_global_indexing_job(
    *,
    job_id: str | None = None,
) -> None:
    """
    Background job: index all globally unindexed READY embeddings.

    Processes across all users and documents in batches.
    Safe to run periodically as a catch-up sweep.

    Args:
        job_id: Optional operational tracing identifier.
    """
    job_id = job_id or str(uuid.uuid4())
    logger.info(
        "global_indexing_job — started: job_id=%s",
        job_id,
    )

    db = SessionLocal()
    try:
        service = VectorIndexingService.create()
        result = service.index_all_pending(db, job_id=job_id)
        logger.info(
            "global_indexing_job — completed: "
            "total=%d indexed=%d skipped=%d failed=%d "
            "index_size=%d job_id=%s duration_s=%.3f",
            result.total,
            result.indexed,
            result.skipped,
            result.failed,
            result.index_size,
            job_id,
            result.duration_s,
        )
    except Exception as exc:
        logger.exception(
            "global_indexing_job — failed: job_id=%s error=%s",
            job_id,
            exc,
        )
    finally:
        db.close()


def run_vector_rebuild_job(
    *,
    job_id: str | None = None,
) -> None:
    """
    Background job: rebuild the entire FAISS index from PostgreSQL.

    Safe rebuild — old index is preserved if rebuild fails.

    Args:
        job_id: Optional operational tracing identifier.
    """
    job_id = job_id or str(uuid.uuid4())
    logger.info(
        "vector_rebuild_job — started: job_id=%s",
        job_id,
    )

    db = SessionLocal()
    try:
        service = VectorIndexingService.create()
        result = service.rebuild_index(db, job_id=job_id)
        logger.info(
            "vector_rebuild_job — completed: "
            "total=%d indexed=%d failed=%d index_size=%d job_id=%s duration_s=%.3f",
            result.total,
            result.indexed,
            result.failed,
            result.index_size,
            job_id,
            result.duration_s,
        )
    except Exception as exc:
        logger.exception(
            "vector_rebuild_job — failed: job_id=%s error=%s",
            job_id,
            exc,
        )
    finally:
        db.close()


def run_vector_reconciliation_job(
    *,
    job_id: str | None = None,
) -> None:
    """
    Background job: detect PostgreSQL ↔ FAISS consistency issues.

    Reports discrepancies but does NOT auto-fix.
    Use run_vector_rebuild_job() to correct major inconsistencies.

    Args:
        job_id: Optional operational tracing identifier.
    """
    job_id = job_id or str(uuid.uuid4())
    logger.info(
        "vector_reconciliation_job — started: job_id=%s",
        job_id,
    )

    db = SessionLocal()
    try:
        service = VectorIndexingService.create()
        result = service.reconcile(db, job_id=job_id)
        level = logger.info if result.is_consistent else logger.warning
        level(
            "vector_reconciliation_job — completed: "
            "consistent=%s db_indexed=%d faiss_vectors=%d "
            "missing_in_faiss=%d orphaned_in_faiss=%d stale=%d job_id=%s",
            result.is_consistent,
            result.db_indexed_count,
            result.faiss_vector_count,
            result.missing_in_faiss,
            result.orphaned_in_faiss,
            result.stale_entries,
            job_id,
        )
    except Exception as exc:
        logger.exception(
            "vector_reconciliation_job — failed: job_id=%s error=%s",
            job_id,
            exc,
        )
    finally:
        db.close()
