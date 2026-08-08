"""
embedding_generation_job — Background embedding generation runner (Day 69 Part A1+A2).

Provides background-task-compatible functions that run the embedding pipeline
in a fresh database session, following the established project pattern.

Usage (FastAPI BackgroundTasks)::

    background_tasks.add_task(
        run_embedding_generation_job,
        document_id=doc.id,
        user_id=current_user.id,
    )

The job handles its own session lifecycle. Callers do NOT pass a db session.
"""
from __future__ import annotations

import logging
import uuid

from app.core.database import SessionLocal
from app.services.embedding_service import EmbeddingService

logger = logging.getLogger(__name__)


def run_embedding_generation_job(
    *,
    document_id: str,
    user_id: int,
    job_id: str | None = None,
    force_reembed: bool = False,
) -> None:
    """
    Background job: generate and persist embedding vectors for a document.

    Opens its own database session and closes it in a `finally` block.

    Args:
        document_id   : UUID of the parent Document.
        user_id       : Authenticated owner's user ID.
        job_id        : Optional operational tracing identifier.
        force_reembed : If True, archive existing embeddings before generating.
    """
    job_id = job_id or str(uuid.uuid4())
    logger.info(
        "embedding_generation_job — started for document_id=%s user_id=%d job_id=%s",
        document_id,
        user_id,
        job_id,
    )

    db = SessionLocal()
    try:
        service = EmbeddingService.create()
        result = service.generate_embeddings_for_document(
            db,
            document_id=document_id,
            user_id=user_id,
            job_id=job_id,
            force_reembed=force_reembed,
        )
        logger.info(
            "embedding_generation_job — completed: ready=%d failed=%d (model=%s dim=%d) "
            "for document_id=%s job_id=%s",
            result["ready"],
            result["failed"],
            result.get("model", "unknown"),
            result.get("dimension", 0),
            document_id,
            job_id,
        )
    except Exception as exc:
        logger.exception(
            "embedding_generation_job — failed for document_id=%s job_id=%s: %s",
            document_id,
            job_id,
            exc,
        )
    finally:
        db.close()


def run_embedding_retry_job(
    *,
    document_id: str,
    user_id: int,
) -> None:
    """
    Background job: retry generation for FAILED embeddings of a document.
    """
    logger.info(
        "embedding_retry_job — started for document_id=%s user_id=%d",
        document_id,
        user_id,
    )

    db = SessionLocal()
    try:
        service = EmbeddingService.create()
        result = service.reembed_failed(
            db,
            document_id=document_id,
            user_id=user_id,
        )
        logger.info(
            "embedding_retry_job — completed: ready=%d failed=%d for document_id=%s",
            result["ready"],
            result["failed"],
            document_id,
        )
    except Exception as exc:
        logger.exception(
            "embedding_retry_job — failed for document_id=%s: %s",
            document_id,
            exc,
        )
    finally:
        db.close()
