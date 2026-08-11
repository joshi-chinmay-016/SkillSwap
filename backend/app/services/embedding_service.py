"""
EmbeddingService — Orchestration of the embedding generation pipeline (Day 69 Part A1+A2).

Responsibilities:
    - Validate user ownership.
    - Retrieve eligible (READY) chunks.
    - Check idempotency (skip already-embedded chunks).
    - Create PENDING embedding records.
    - Send chunk text to EmbeddingProvider in configurable batches.
    - Validate returned vectors via EmbeddingValidator.
    - Persist vectors to EmbeddingRepository.
    - Handle provider failures with exponential backoff retry.
    - Track processing state per-batch (partial completion support).
    - Collect and expose metrics.

Architecture:
    EmbeddingService
        ↓
    EmbeddingProvider (interface — injected, not hardcoded)
        ↓
    GeminiEmbeddingProvider (concrete implementation)

Business logic belongs here. The repository handles only persistence.
The provider handles only API calls.

Security:
    - Chunk text is never logged.
    - Embedding vectors are never logged.
    - Provider credentials are never accessed here.
    - Ownership is validated before every operation.

Metrics tracked (in-memory, thread-safe):
    embedding_jobs_total
    embedding_chunks_processed
    embedding_chunks_failed
    embedding_generation_latency_ms_total
    provider_errors
    rate_limit_events
    retry_count
    batch_count
"""
from __future__ import annotations

import logging
import time
import uuid
from threading import Lock

from sqlalchemy.orm import Session

from app.embeddings.embedding_provider import EmbeddingProvider
from app.embeddings.embedding_result import (
    EMBEDDING_STATUS_FAILED,
    EMBEDDING_STATUS_PROCESSING,
    EMBEDDING_STATUS_READY,
    BatchEmbeddingResult,
    EmbeddingResult,
)
from app.exceptions.embedding_exceptions import (
    EmbeddingConfigurationError,
    EmbeddingIdempotencyError,
    EmbeddingProviderError,
    EmbeddingRateLimitError,
    EmbeddingTimeoutError,
    EmbeddingValidationError,
)
from app.models.chunk import Chunk, ChunkStatus
from app.models.embedding import Embedding, EmbeddingStatus
from app.repositories import embedding_repository as repo
from app.utils.embedding_validator import validate_vector

logger = logging.getLogger(__name__)


# ── In-memory metrics ─────────────────────────────────────────────────────────

_METRICS_LOCK = Lock()
_METRICS: dict[str, float] = {
    "embedding_jobs_total": 0,
    "embedding_chunks_processed": 0,
    "embedding_chunks_failed": 0,
    "embedding_generation_latency_ms_total": 0.0,
    "provider_errors": 0,
    "rate_limit_events": 0,
    "retry_count": 0,
    "batch_count": 0,
}


def _inc(key: str, value: float = 1.0) -> None:
    with _METRICS_LOCK:
        _METRICS[key] += value


# ── Error category helpers ─────────────────────────────────────────────────────

def _categorise_error(exc: Exception) -> str:
    """Map an exception to a normalised error category string."""
    if isinstance(exc, EmbeddingRateLimitError):
        return "rate_limit"
    if isinstance(exc, EmbeddingTimeoutError):
        return "timeout"
    if isinstance(exc, EmbeddingValidationError):
        return "validation_error"
    if isinstance(exc, EmbeddingConfigurationError):
        return "configuration_error"
    return "provider_error"


# ── Retry helpers ──────────────────────────────────────────────────────────────

def _with_retry(
    fn,
    *,
    max_retries: int,
    base_delay: float = 1.0,
    job_id: str | None = None,
) -> list[list[float]]:
    """
    Call fn() with exponential-backoff retry for recoverable failures.

    Args:
        fn          : Zero-argument callable returning list[list[float]].
        max_retries : Maximum number of retry attempts (0 = no retry).
        base_delay  : Initial delay in seconds (doubles each retry).
        job_id      : For log context.

    Returns:
        Result of fn().

    Raises:
        The last exception if all attempts fail.
    """
    attempt = 0
    last_exc: Exception | None = None

    while attempt <= max_retries:
        try:
            return fn()
        except Exception as exc:
            last_exc = exc
            if not getattr(exc, "is_recoverable", False):
                raise  # Non-recoverable — don't retry

            attempt += 1
            _inc("retry_count")

            if isinstance(exc, EmbeddingRateLimitError):
                _inc("rate_limit_events")

            if attempt > max_retries:
                break

            delay = base_delay * (2 ** (attempt - 1))
            logger.warning(
                "EmbeddingService — retry %d/%d after %.1fs. "
                "job_id=%s error=%s: %s",
                attempt,
                max_retries,
                delay,
                job_id,
                type(exc).__name__,
                str(exc)[:120],
            )
            time.sleep(delay)

    raise last_exc  # type: ignore[misc]


# ── Service ────────────────────────────────────────────────────────────────────

class EmbeddingService:
    """
    Orchestrates the full embedding generation → validation → persistence pipeline.

    All public methods:
        - Validate user ownership.
        - Use EmbeddingRepository for persistence.
        - Use EmbeddingProvider for vector generation.
        - Never expose raw vectors or chunk text in logs.
        - Commit per batch to support partial completion.
    """

    def __init__(self, provider: EmbeddingProvider) -> None:
        """
        Args:
            provider: An EmbeddingProvider implementation. Injected — not hardcoded.
        """
        self._provider = provider

    # ── Main pipeline ──────────────────────────────────────────────────────────

    @classmethod
    def create(cls) -> "EmbeddingService":
        """
        Factory method: construct EmbeddingService with the configured provider.

        Reads EMBEDDING_PROVIDER from settings to select the implementation.
        Currently only 'gemini' is supported.
        """
        from app.core.config import settings
        from app.embeddings.providers.gemini_embedding_provider import GeminiEmbeddingProvider

        provider_name = getattr(settings, "EMBEDDING_PROVIDER", "gemini").lower()
        if provider_name == "gemini":
            provider = GeminiEmbeddingProvider()
        else:
            raise EmbeddingConfigurationError(
                f"Unsupported EMBEDDING_PROVIDER={provider_name!r}. "
                "Only 'gemini' is currently supported."
            )
        return cls(provider=provider)

    def generate_embeddings_for_document(
        self,
        db: Session,
        *,
        document_id: str,
        user_id: int,
        job_id: str | None = None,
        force_reembed: bool = False,
    ) -> dict:
        """
        Generate embeddings for all READY chunks of a document.

        Flow:
            1. Validate ownership.
            2. Resolve parsed_document_id.
            3. Find chunks without a READY embedding (partial completion support).
            4. Create PENDING embedding records.
            5. Process in batches.
            6. Commit per batch.

        Args:
            db           : Active SQLAlchemy session.
            document_id  : Parent Document UUID.
            user_id      : Authenticated user ID.
            job_id       : Optional tracing identifier (auto-generated if None).
            force_reembed: If True, archive existing READY embeddings first.

        Returns:
            Summary dict with job_id, chunk_count, ready, failed counts.
        """
        from app.core.config import settings
        from app.repositories.parsed_document_repository import get_parsed_document

        job_id = job_id or str(uuid.uuid4())
        _inc("embedding_jobs_total")

        logger.info(
            "EmbeddingService.generate_embeddings_for_document — "
            "job_id=%s document_id=%s user_id=%d",
            job_id, document_id, user_id,
        )

        # Step 1: Ownership validation
        self._assert_document_ownership(db, document_id, user_id)

        # Step 2: Resolve parsed document
        parsed = get_parsed_document(db, document_id)
        if not parsed:
            raise ValueError(
                f"No ParsedDocument found for document_id={document_id}."
            )
        parsed_document_id = parsed.id

        model_name = self._provider.get_model_name()
        model_version = self._provider.get_model_version()
        provider_name = self._provider.provider_name
        dimension = self._provider.get_dimension()
        embedding_version = int(getattr(settings, "EMBEDDING_VERSION", 1))
        batch_size = int(getattr(settings, "EMBEDDING_BATCH_SIZE", 32))
        max_retries = int(getattr(settings, "EMBEDDING_MAX_RETRIES", 3))

        # Step 3: If force_reembed, archive existing READY embeddings and bump embedding_version if needed
        if force_reembed:
            from app.models.chunk import Chunk, ChunkStatus
            ready_chunk_ids = [
                row[0]
                for row in db.query(Chunk.id).filter(
                    Chunk.parsed_document_id == parsed_document_id,
                    Chunk.status == ChunkStatus.READY.value,
                ).all()
            ]
            if ready_chunk_ids:
                archived = repo.bulk_archive_embeddings(
                    db,
                    ready_chunk_ids,
                    provider=provider_name,
                    model_name=model_name,
                )
                db.commit()
                # If an embedding with current embedding_version was archived, increment version to prevent UNIQUE constraint violation
                embedding_version += 1
                logger.info(
                    "EmbeddingService — force_reembed: archived %d embeddings, bumped embedding_version to %d. "
                    "job_id=%s document_id=%s",
                    archived, embedding_version, job_id, document_id,
                )

        # Step 4: Find chunks that need embedding
        chunk_ids_needed = repo.get_chunks_without_ready_embedding(
            db,
            parsed_document_id,
            provider=provider_name,
            model_name=model_name,
            model_version=model_version,
            embedding_version=embedding_version,
        )

        if not chunk_ids_needed:
            logger.info(
                "EmbeddingService — all chunks already embedded. "
                "job_id=%s document_id=%s",
                job_id, document_id,
            )
            return {
                "job_id": job_id,
                "document_id": document_id,
                "parsed_document_id": parsed_document_id,
                "chunk_count": 0,
                "ready": 0,
                "failed": 0,
                "skipped": 0,
                "message": "All chunks already have READY embeddings.",
            }

        # Step 5: Fetch Chunk ORM objects
        from app.models.chunk import Chunk
        chunks: list[Chunk] = (
            db.query(Chunk)
            .filter(Chunk.id.in_(chunk_ids_needed))
            .order_by(Chunk.chunk_index)
            .all()
        )

        logger.info(
            "EmbeddingService — processing %d chunks in batches of %d. "
            "job_id=%s document_id=%s model=%s",
            len(chunks), batch_size, job_id, document_id, model_name,
        )

        # Step 6: Create PENDING embedding records (before batching)
        pending_records = [
            {
                "chunk_id": chunk.id,
                "parsed_document_id": parsed_document_id,
                "user_id": user_id,
                "provider": provider_name,
                "model_name": model_name,
                "model_version": model_version,
                "embedding_version": embedding_version,
                "dimension": dimension,
                "status": EmbeddingStatus.PENDING.value,
            }
            for chunk in chunks
        ]
        embedding_objects = repo.bulk_create_embeddings(db, records=pending_records)
        db.commit()

        # Build lookup: chunk_id → Embedding
        chunk_to_embedding: dict[str, Embedding] = {
            emb.chunk_id: emb for emb in embedding_objects
        }

        # Step 7: Process in batches
        batches = _make_batches(chunks, batch_size)
        total_ready = 0
        total_failed = 0
        job_start = time.monotonic()

        for batch_index, batch_chunks in enumerate(batches):
            batch_id = f"{job_id}-b{batch_index}"
            batch_result = self._process_batch(
                db,
                chunks=batch_chunks,
                chunk_to_embedding=chunk_to_embedding,
                provider=self._provider,
                dimension=dimension,
                max_retries=max_retries,
                job_id=job_id,
                batch_id=batch_id,
                batch_index=batch_index,
            )
            total_ready += batch_result.ready_count
            total_failed += batch_result.failed_count
            db.commit()

            _inc("batch_count")
            logger.info(
                "EmbeddingService — batch %d/%d complete: "
                "ready=%d failed=%d. job_id=%s document_id=%s",
                batch_index + 1, len(batches),
                batch_result.ready_count, batch_result.failed_count,
                job_id, document_id,
            )

        duration_ms = (time.monotonic() - job_start) * 1000
        _inc("embedding_generation_latency_ms_total", duration_ms)

        logger.info(
            "EmbeddingService — job complete: ready=%d failed=%d "
            "duration_ms=%.1f job_id=%s document_id=%s model=%s",
            total_ready, total_failed, duration_ms, job_id, document_id, model_name,
        )

        return {
            "job_id": job_id,
            "document_id": document_id,
            "parsed_document_id": parsed_document_id,
            "model": model_name,
            "dimension": dimension,
            "embedding_version": embedding_version,
            "chunk_count": len(chunks),
            "ready": total_ready,
            "failed": total_failed,
            "skipped": 0,
            "duration_ms": round(duration_ms, 1),
            "message": (
                f"Generated {total_ready} embeddings. "
                f"{total_failed} failed."
            ),
        }

    def reembed_document(
        self,
        db: Session,
        *,
        document_id: str,
        user_id: int,
    ) -> dict:
        """
        Archive all existing READY embeddings and regenerate for a document.

        Useful after a model upgrade or embedding version bump.
        """
        return self.generate_embeddings_for_document(
            db,
            document_id=document_id,
            user_id=user_id,
            force_reembed=True,
        )

    def reembed_failed(
        self,
        db: Session,
        *,
        document_id: str,
        user_id: int,
    ) -> dict:
        """
        Retry generation only for FAILED embedding records.

        Does not touch READY or PENDING embeddings.
        """
        from app.core.config import settings
        from app.repositories.parsed_document_repository import get_parsed_document

        job_id = str(uuid.uuid4())

        self._assert_document_ownership(db, document_id, user_id)

        parsed = get_parsed_document(db, document_id)
        if not parsed:
            raise ValueError(f"No ParsedDocument found for document_id={document_id}.")

        failed_embeddings = repo.list_failed_embeddings(db, parsed.id)
        if not failed_embeddings:
            return {
                "job_id": job_id,
                "document_id": document_id,
                "chunk_count": 0,
                "ready": 0,
                "failed": 0,
                "message": "No FAILED embeddings found.",
            }

        # Collect the chunk IDs from failed embeddings and re-run
        failed_chunk_ids = {emb.chunk_id for emb in failed_embeddings}
        from app.models.chunk import Chunk
        chunks = (
            db.query(Chunk)
            .filter(Chunk.id.in_(failed_chunk_ids))
            .order_by(Chunk.chunk_index)
            .all()
        )

        batch_size = int(getattr(settings, "EMBEDDING_BATCH_SIZE", 32))
        max_retries = int(getattr(settings, "EMBEDDING_MAX_RETRIES", 3))
        dimension = self._provider.get_dimension()

        chunk_to_embedding: dict[str, Embedding] = {
            emb.chunk_id: emb for emb in failed_embeddings
        }

        total_ready = 0
        total_failed = 0
        batches = _make_batches(chunks, batch_size)

        for batch_index, batch_chunks in enumerate(batches):
            # Reset FAILED → PROCESSING before retry
            for chunk in batch_chunks:
                if chunk.id in chunk_to_embedding:
                    repo.update_embedding_status(
                        db, chunk_to_embedding[chunk.id], EmbeddingStatus.PROCESSING.value
                    )
            db.flush()

            batch_result = self._process_batch(
                db,
                chunks=batch_chunks,
                chunk_to_embedding=chunk_to_embedding,
                provider=self._provider,
                dimension=dimension,
                max_retries=max_retries,
                job_id=job_id,
                batch_id=f"{job_id}-b{batch_index}",
                batch_index=batch_index,
            )
            total_ready += batch_result.ready_count
            total_failed += batch_result.failed_count
            db.commit()

        return {
            "job_id": job_id,
            "document_id": document_id,
            "parsed_document_id": parsed.id,
            "chunk_count": len(chunks),
            "ready": total_ready,
            "failed": total_failed,
            "message": f"Retry complete. {total_ready} succeeded, {total_failed} still failed.",
        }

    def get_embedding_status(
        self,
        db: Session,
        *,
        document_id: str,
        user_id: int,
    ) -> dict:
        """
        Return the embedding status summary for a document.

        Returns only metadata — never vectors.
        """
        from app.repositories.parsed_document_repository import get_parsed_document

        self._assert_document_ownership(db, document_id, user_id)

        parsed = get_parsed_document(db, document_id)
        if not parsed:
            return {"document_id": document_id, "error": "ParsedDocument not found."}

        ready = repo.count_embeddings_by_document(
            db, parsed.id, status_filter=EmbeddingStatus.READY.value
        )
        pending = repo.count_embeddings_by_document(
            db, parsed.id, status_filter=EmbeddingStatus.PENDING.value
        )
        processing = repo.count_embeddings_by_document(
            db, parsed.id, status_filter=EmbeddingStatus.PROCESSING.value
        )
        failed = repo.count_embeddings_by_document(
            db, parsed.id, status_filter=EmbeddingStatus.FAILED.value
        )
        archived = repo.count_embeddings_by_document(
            db, parsed.id, status_filter=EmbeddingStatus.ARCHIVED.value
        )

        return {
            "document_id": document_id,
            "parsed_document_id": parsed.id,
            "model": self._provider.get_model_name(),
            "dimension": self._provider.get_dimension(),
            "ready": ready,
            "pending": pending,
            "processing": processing,
            "failed": failed,
            "archived": archived,
            "total_active": ready + pending + processing + failed,
        }

    # ── Metrics ────────────────────────────────────────────────────────────────

    @staticmethod
    def get_metrics() -> dict:
        """Return current in-memory metrics snapshot."""
        with _METRICS_LOCK:
            return dict(_METRICS)

    # ── Internal helpers ───────────────────────────────────────────────────────

    def _process_batch(
        self,
        db: Session,
        *,
        chunks: list[Chunk],
        chunk_to_embedding: dict[str, Embedding],
        provider: EmbeddingProvider,
        dimension: int,
        max_retries: int,
        job_id: str,
        batch_id: str,
        batch_index: int,
    ) -> BatchEmbeddingResult:
        """
        Process a single batch: mark PROCESSING → call provider → validate → persist.

        Each batch is fully self-contained. If the batch fails after all retries,
        the chunks in it are marked FAILED without affecting other batches.
        """
        batch_result = BatchEmbeddingResult(
            batch_index=batch_index,
            job_id=job_id,
            batch_id=batch_id,
        )

        # Mark all as PROCESSING
        for chunk in chunks:
            if chunk.id in chunk_to_embedding:
                repo.update_embedding_status(
                    db,
                    chunk_to_embedding[chunk.id],
                    EmbeddingStatus.PROCESSING.value,
                )
        db.flush()

        texts = [chunk.chunk_text for chunk in chunks]
        batch_start = time.monotonic()

        try:
            vectors = _with_retry(
                lambda: provider.generate_embeddings(texts),
                max_retries=max_retries,
                job_id=job_id,
            )
        except EmbeddingRateLimitError as exc:
            _inc("rate_limit_events")
            _inc("provider_errors")
            return self._fail_batch(
                db, chunks, chunk_to_embedding, "rate_limit", batch_result, exc
            )
        except EmbeddingTimeoutError as exc:
            _inc("provider_errors")
            return self._fail_batch(
                db, chunks, chunk_to_embedding, "timeout", batch_result, exc
            )
        except EmbeddingProviderError as exc:
            _inc("provider_errors")
            return self._fail_batch(
                db, chunks, chunk_to_embedding, "provider_error", batch_result, exc
            )
        except Exception as exc:
            _inc("provider_errors")
            return self._fail_batch(
                db, chunks, chunk_to_embedding, "provider_error", batch_result, exc
            )

        duration_ms = (time.monotonic() - batch_start) * 1000

        # Validate and persist per-vector
        if len(vectors) != len(chunks):
            logger.error(
                "EmbeddingService — batch %d vector count mismatch: "
                "expected=%d got=%d. job_id=%s",
                batch_index, len(chunks), len(vectors), job_id,
            )
            return self._fail_batch(
                db, chunks, chunk_to_embedding, "validation_error", batch_result,
                ValueError(f"Provider returned {len(vectors)} vectors for {len(chunks)} chunks."),
            )

        for chunk, vector in zip(chunks, vectors):
            chunk_id = chunk.id
            emb = chunk_to_embedding.get(chunk_id)
            if emb is None:
                continue

            # Validate
            try:
                validate_vector(vector, dimension, chunk_id=chunk_id)
            except EmbeddingValidationError as exc:
                logger.warning(
                    "EmbeddingService — validation failed for chunk_id=%s: %s. "
                    "job_id=%s",
                    chunk_id, str(exc)[:120], job_id,
                )
                repo.update_embedding_status(
                    db, emb, EmbeddingStatus.FAILED.value,
                    error_category="validation_error",
                    increment_failure=True,
                )
                _inc("embedding_chunks_failed")
                batch_result.results.append(
                    EmbeddingResult(
                        chunk_id=chunk_id,
                        vector=[],
                        provider=provider.provider_name,
                        model_name=provider.get_model_name(),
                        model_version=provider.get_model_version(),
                        dimension=dimension,
                        embedding_version=emb.embedding_version,
                        status=EMBEDDING_STATUS_FAILED,
                        error_category="validation_error",
                        job_id=job_id,
                        batch_id=batch_id,
                    )
                )
                continue

            # Persist vector
            repo.update_embedding_vector(db, emb, vector, status=EmbeddingStatus.READY.value)
            _inc("embedding_chunks_processed")

            per_chunk_ms = duration_ms / max(len(chunks), 1)
            batch_result.results.append(
                EmbeddingResult(
                    chunk_id=chunk_id,
                    vector=vector,
                    provider=provider.provider_name,
                    model_name=provider.get_model_name(),
                    model_version=provider.get_model_version(),
                    dimension=dimension,
                    embedding_version=emb.embedding_version,
                    status=EMBEDDING_STATUS_READY,
                    duration_ms=per_chunk_ms,
                    job_id=job_id,
                    batch_id=batch_id,
                )
            )

        return batch_result

    def _fail_batch(
        self,
        db: Session,
        chunks: list[Chunk],
        chunk_to_embedding: dict[str, Embedding],
        error_category: str,
        batch_result: BatchEmbeddingResult,
        exc: Exception,
    ) -> BatchEmbeddingResult:
        """Mark all chunks in a batch as FAILED."""
        logger.error(
            "EmbeddingService — batch %d failed: %s — %s. job_id=%s",
            batch_result.batch_index, type(exc).__name__, str(exc)[:120],
            batch_result.job_id,
        )
        provider = self._provider
        for chunk in chunks:
            emb = chunk_to_embedding.get(chunk.id)
            if emb:
                repo.update_embedding_status(
                    db, emb, EmbeddingStatus.FAILED.value,
                    error_category=error_category,
                    increment_failure=True,
                )
            _inc("embedding_chunks_failed")
            batch_result.results.append(
                EmbeddingResult(
                    chunk_id=chunk.id,
                    vector=[],
                    provider=provider.provider_name,
                    model_name=provider.get_model_name(),
                    model_version=provider.get_model_version(),
                    dimension=provider.get_dimension(),
                    embedding_version=int(
                        getattr(emb, "embedding_version", 1) if emb else 1
                    ),
                    status=EMBEDDING_STATUS_FAILED,
                    error_category=error_category,
                    job_id=batch_result.job_id,
                    batch_id=batch_result.batch_id,
                )
            )
        db.flush()
        return batch_result

    @staticmethod
    def _assert_document_ownership(
        db: Session,
        document_id: str,
        user_id: int,
    ) -> None:
        """Raise ValueError if document does not belong to user_id."""
        from app.models.document import Document

        document = db.query(Document).filter_by(id=document_id).first()
        if not document:
            raise ValueError(f"Document {document_id} not found.")
        if document.user_id != user_id:
            raise ValueError(
                f"Document {document_id} does not belong to user {user_id}."
            )


# ── Batch helpers ──────────────────────────────────────────────────────────────

def _make_batches(items: list, batch_size: int) -> list[list]:
    """Split a list into sub-lists of at most batch_size items."""
    if batch_size <= 0:
        return [items]
    return [items[i : i + batch_size] for i in range(0, len(items), batch_size)]
