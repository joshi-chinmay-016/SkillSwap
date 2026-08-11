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

Auto-retry behaviour
--------------------
When ``EMBEDDING_AUTO_RETRY=true`` (the default), any chunks that are still
``FAILED`` after the main embedding pass are automatically retried in a daemon
background thread after ``EMBEDDING_AUTO_RETRY_DELAY_SECONDS`` (default 30 s).
This gives transient errors (rate-limits, timeouts, network blips) time to
clear before the retry fires.  Only **one** automatic retry pass is scheduled —
chunks that still fail after the retry remain ``FAILED`` for manual inspection.
"""
from __future__ import annotations

import logging
import threading
import time
import uuid

from app.core.database import SessionLocal
from app.services.embedding_service import EmbeddingService

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _schedule_auto_retry(
    *,
    document_id: str,
    user_id: int,
    delay_seconds: int,
    parent_job_id: str,
) -> None:
    """
    Launch a daemon thread that sleeps ``delay_seconds`` then calls
    ``run_embedding_retry_job``.  The thread is daemonised so it never blocks
    server shutdown.
    """
    def _worker() -> None:
        logger.info(
            "embedding_auto_retry — waiting %ds before retry for "
            "document_id=%s parent_job_id=%s",
            delay_seconds, document_id, parent_job_id,
        )
        time.sleep(delay_seconds)
        logger.info(
            "embedding_auto_retry — starting retry for document_id=%s "
            "parent_job_id=%s",
            document_id, parent_job_id,
        )
        run_embedding_retry_job(
            document_id=document_id,
            user_id=user_id,
        )

    thread = threading.Thread(target=_worker, daemon=True, name=f"emb-auto-retry-{parent_job_id[:8]}")
    thread.start()
    logger.info(
        "embedding_auto_retry — scheduled daemon thread (delay=%ds) for "
        "document_id=%s parent_job_id=%s",
        delay_seconds, document_id, parent_job_id,
    )


# ---------------------------------------------------------------------------
# Public job functions
# ---------------------------------------------------------------------------

def run_embedding_generation_job(
    *,
    document_id: str,
    user_id: int,
    job_id: str | None = None,
    force_reembed: bool = False,
) -> None:
    """
    Background job: generate and persist embedding vectors for a document.

    Opens its own database session and closes it in a ``finally`` block.

    After the main pass completes, if any chunks are still ``FAILED`` **and**
    ``EMBEDDING_AUTO_RETRY=true``, a single automatic retry pass is scheduled
    in a daemon thread after ``EMBEDDING_AUTO_RETRY_DELAY_SECONDS``.

    Args:
        document_id   : UUID of the parent Document.
        user_id       : Authenticated owner's user ID.
        job_id        : Optional operational tracing identifier.
        force_reembed : If True, archive existing embeddings before generating.
    """
    from app.core.config import settings

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

        ready_count = result.get("ready", 0)
        failed_count = result.get("failed", 0)

        logger.info(
            "embedding_generation_job — completed: ready=%d failed=%d (model=%s dim=%d) "
            "for document_id=%s job_id=%s",
            ready_count,
            failed_count,
            result.get("model", "unknown"),
            result.get("dimension", 0),
            document_id,
            job_id,
        )

        # ── Chain to vector indexing if any chunks are ready ───────────────
        parsed_doc_id = result.get("parsed_document_id")
        if parsed_doc_id and ready_count > 0:
            from app.jobs.vector_indexing_job import run_vector_indexing_job
            logger.info(
                "embedding_generation_job — triggering vector_indexing_job for "
                "parsed_document_id=%s user_id=%d",
                parsed_doc_id,
                user_id,
            )
            run_vector_indexing_job(
                parsed_document_id=parsed_doc_id,
                user_id=user_id,
                job_id=job_id,
            )

        # ── Auto-retry failed chunks ────────────────────────────────────────
        auto_retry_enabled: bool = getattr(settings, "EMBEDDING_AUTO_RETRY", True)
        if failed_count > 0 and auto_retry_enabled:
            delay: int = int(getattr(settings, "EMBEDDING_AUTO_RETRY_DELAY_SECONDS", 30))
            logger.warning(
                "embedding_generation_job — %d chunk(s) failed; scheduling automatic "
                "retry in %ds for document_id=%s job_id=%s",
                failed_count, delay, document_id, job_id,
            )
            _schedule_auto_retry(
                document_id=document_id,
                user_id=user_id,
                delay_seconds=delay,
                parent_job_id=job_id,
            )
        elif failed_count > 0:
            logger.warning(
                "embedding_generation_job — %d chunk(s) failed and "
                "EMBEDDING_AUTO_RETRY is disabled. document_id=%s job_id=%s",
                failed_count, document_id, job_id,
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

    Called automatically by ``_schedule_auto_retry`` when
    ``EMBEDDING_AUTO_RETRY=true``, or manually via the API endpoint.
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
        ready_count = result.get("ready", 0)
        failed_count = result.get("failed", 0)

        logger.info(
            "embedding_retry_job — completed: ready=%d failed=%d for document_id=%s",
            ready_count,
            failed_count,
            document_id,
        )

        # Chain to vector indexing if the retry rescued some chunks
        parsed_doc_id = result.get("parsed_document_id")
        if parsed_doc_id and ready_count > 0:
            from app.jobs.vector_indexing_job import run_vector_indexing_job
            logger.info(
                "embedding_retry_job — triggering vector_indexing_job for "
                "parsed_document_id=%s user_id=%d",
                parsed_doc_id,
                user_id,
            )
            run_vector_indexing_job(
                parsed_document_id=parsed_doc_id,
                user_id=user_id,
            )

        if failed_count > 0:
            logger.warning(
                "embedding_retry_job — %d chunk(s) still FAILED after automatic "
                "retry for document_id=%s. Manual intervention may be required.",
                failed_count, document_id,
            )

    except Exception as exc:
        logger.exception(
            "embedding_retry_job — failed for document_id=%s: %s",
            document_id,
            exc,
        )
    finally:
        db.close()
