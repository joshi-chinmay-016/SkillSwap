"""
VectorIndexingService — Orchestrates moving READY embeddings into FAISS (Day 70 Part A2).

Responsibilities:
    - Load READY embeddings not yet in FAISS from PostgreSQL.
    - Validate vectors before indexing.
    - Batch-index into FAISSVectorStore.
    - Maintain VectorIndexEntry records for idempotency and reconciliation.
    - Handle partial batch failures safely.
    - Atomic FAISS persistence after each batch.
    - Document-level and global indexing.
    - Safe index rebuild.
    - Consistency reconciliation between PostgreSQL and FAISS.
    - Remove archived/deleted vectors.

Architecture:
    VectorIndexingService
        ├── EmbeddingRepository   (read READY embeddings)
        ├── VectorIndexRepository (read/write indexing status in PostgreSQL)
        └── VectorStore           (FAISSVectorStore — injected)

Security:
    - Raw vector values are never logged.
    - User ownership is validated before document-level operations.
    - FAISS does not enforce access control — the service layer does.

Transaction ordering (per batch):
    1. Identify unindexed READY embeddings.
    2. Add vectors to FAISS in-memory.
    3. Persist FAISS index to disk (atomic).
    4. Update vector_index_entries in PostgreSQL.
    5. db.commit().

    Failure between step 3 and 5 leaves FAISS ahead of PostgreSQL.
    Reconciliation re-adds the missing PostgreSQL entries on next run.
    Failure before step 3 means vectors are not durably stored.
"""
from __future__ import annotations

import logging
import time
import uuid
from dataclasses import dataclass, field
from threading import Lock
from typing import Optional

import numpy as np

from sqlalchemy.orm import Session

from app.models.embedding import Embedding, EmbeddingStatus
from app.models.vector_index_entry import VectorIndexStatus
from app.repositories import embedding_repository as emb_repo
from app.repositories import vector_index_repository as vidx_repo
from app.vector_store.base import VectorStore
from app.vector_store.exceptions import (
    FAISSIndexError,
    VectorConsistencyError,
    VectorDimensionMismatchError,
    VectorIndexingError,
    VectorRebuildError,
    VectorStoreError,
    VectorStoreInitializationError,
    VectorStorePersistenceError,
)

logger = logging.getLogger(__name__)

# ── Numpy dtype FAISS expects ─────────────────────────────────────────────────
_NUMPY_DTYPE = np.float32

# ── Service-level metrics lock ────────────────────────────────────────────────
_METRICS_LOCK = Lock()
_METRICS: dict[str, float] = {
    "indexing_jobs_total": 0,
    "vectors_indexed_total": 0,
    "vectors_skipped_total": 0,
    "vectors_failed_total": 0,
    "rebuild_jobs_total": 0,
    "reconciliation_jobs_total": 0,
}


def _inc(key: str, value: float = 1.0) -> None:
    with _METRICS_LOCK:
        _METRICS[key] += value


# ── Result dataclass ──────────────────────────────────────────────────────────

@dataclass
class IndexingResult:
    """
    Structured result from a VectorIndexingService operation.

    Fields:
        total      : Total eligible embeddings considered.
        processed  : Embeddings actually processed (attempted).
        indexed    : Successfully added to FAISS and recorded in DB.
        skipped    : Already indexed (idempotency skip).
        failed     : Failed to index (logged individually).
        duration_s : Wall-clock time in seconds.
        index_size : Total vectors in FAISS after the operation.
        job_id     : Operational tracing identifier.
    """

    total: int = 0
    processed: int = 0
    indexed: int = 0
    skipped: int = 0
    failed: int = 0
    duration_s: float = 0.0
    index_size: int = 0
    job_id: str = field(default_factory=lambda: str(uuid.uuid4()))

    def as_dict(self) -> dict:
        return {
            "job_id": self.job_id,
            "total": self.total,
            "processed": self.processed,
            "indexed": self.indexed,
            "skipped": self.skipped,
            "failed": self.failed,
            "duration_s": round(self.duration_s, 3),
            "index_size": self.index_size,
        }


@dataclass
class ReconciliationResult:
    """
    Result of a PostgreSQL ↔ FAISS consistency check.

    Fields:
        db_indexed_count    : INDEXED entries in PostgreSQL.
        faiss_vector_count  : Actual vectors in FAISS.
        missing_in_faiss    : Embeddings in DB as INDEXED but no FAISS vector.
        orphaned_in_faiss   : FAISS vectors with no DB mapping entry.
        stale_entries       : DB entries whose embedding is no longer READY.
        is_consistent       : True if all counts match and no issues found.
    """

    db_indexed_count: int = 0
    faiss_vector_count: int = 0
    missing_in_faiss: int = 0
    orphaned_in_faiss: int = 0
    stale_entries: int = 0
    is_consistent: bool = True

    def as_dict(self) -> dict:
        return {
            "db_indexed_count": self.db_indexed_count,
            "faiss_vector_count": self.faiss_vector_count,
            "missing_in_faiss": self.missing_in_faiss,
            "orphaned_in_faiss": self.orphaned_in_faiss,
            "stale_entries": self.stale_entries,
            "is_consistent": self.is_consistent,
        }


# ── Service ───────────────────────────────────────────────────────────────────

class VectorIndexingService:
    """
    Orchestrates the embedding → FAISS vector indexing pipeline.

    All public methods:
        - Accept a SQLAlchemy Session (caller manages transaction lifecycle).
        - Never expose raw vectors in logs.
        - Return structured result objects.
        - Never perform similarity search (that belongs to Day 71 Retriever).
    """

    def __init__(
        self,
        vector_store: VectorStore,
        *,
        batch_size: int = 100,
    ) -> None:
        """
        Args:
            vector_store: An initialised VectorStore implementation.
            batch_size  : Number of embeddings to process per FAISS batch.
        """
        self._store = vector_store
        self._batch_size = batch_size

    # ── Factory ───────────────────────────────────────────────────────────────

    @classmethod
    def create(cls) -> "VectorIndexingService":
        """
        Factory: construct VectorIndexingService using application settings.

        Initialises FAISSVectorStore from settings, then initialises the index.
        Reads FAISS_INDEXING_BATCH_SIZE from settings.

        Returns:
            Ready-to-use VectorIndexingService.

        Raises:
            VectorStoreInitializationError: FAISS index cannot be initialised.
        """
        from app.core.config import settings
        from app.vector_store.faiss_store import FAISSVectorStore

        batch_size: int = getattr(settings, "FAISS_INDEXING_BATCH_SIZE", 100)
        store = FAISSVectorStore.from_settings()
        store.initialize_index()
        return cls(vector_store=store, batch_size=batch_size)

    # ── Main indexing pipeline ─────────────────────────────────────────────────

    def index_document(
        self,
        db: Session,
        *,
        parsed_document_id: str,
        user_id: int,
        job_id: str | None = None,
    ) -> IndexingResult:
        """
        Index all READY embeddings for a specific document.

        Enforces user ownership — only embeddings owned by user_id are indexed.

        Args:
            db                 : Active SQLAlchemy session.
            parsed_document_id : The ParsedDocument UUID to index.
            user_id            : Authenticated owner's user ID.
            job_id             : Optional tracing identifier.

        Returns:
            IndexingResult with per-operation counters.
        """
        job_id = job_id or str(uuid.uuid4())
        logger.info(
            "VectorIndexingService.index_document — started: "
            "parsed_document_id=%s user_id=%d job_id=%s",
            parsed_document_id,
            user_id,
            job_id,
        )
        start = time.monotonic()
        _inc("indexing_jobs_total")

        result = IndexingResult(job_id=job_id)

        # Fetch eligible embeddings for this document
        candidates = vidx_repo.list_unindexed_ready_embeddings(
            db,
            parsed_document_id=parsed_document_id,
            user_id=user_id,
        )
        result.total = len(candidates)

        if not candidates:
            logger.info(
                "VectorIndexingService.index_document — no unindexed embeddings "
                "for parsed_document_id=%s job_id=%s",
                parsed_document_id,
                job_id,
            )
            result.index_size = self._store.get_index_size()
            result.duration_s = time.monotonic() - start
            return result

        self._index_batch_list(db, candidates, result, job_id=job_id)

        result.index_size = self._store.get_index_size()
        result.duration_s = time.monotonic() - start

        logger.info(
            "VectorIndexingService.index_document — completed: "
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
        return result

    def index_all_pending(
        self,
        db: Session,
        *,
        job_id: str | None = None,
    ) -> IndexingResult:
        """
        Index all globally unindexed READY embeddings across all users/documents.

        Processes in batches of self._batch_size to bound memory usage.

        Args:
            db     : Active SQLAlchemy session.
            job_id : Optional tracing identifier.

        Returns:
            IndexingResult with aggregated counters.
        """
        job_id = job_id or str(uuid.uuid4())
        logger.info(
            "VectorIndexingService.index_all_pending — started: job_id=%s "
            "batch_size=%d",
            job_id,
            self._batch_size,
        )
        start = time.monotonic()
        _inc("indexing_jobs_total")

        result = IndexingResult(job_id=job_id)
        batch_num = 0

        while True:
            candidates = vidx_repo.list_unindexed_ready_embeddings(
                db, limit=self._batch_size
            )
            if not candidates:
                break

            result.total += len(candidates)
            batch_num += 1
            logger.info(
                "VectorIndexingService.index_all_pending — batch %d: %d embeddings "
                "job_id=%s",
                batch_num,
                len(candidates),
                job_id,
            )
            self._index_batch_list(db, candidates, result, job_id=job_id)

            # Avoid infinite loop if all candidates are failing
            if result.failed > 0 and result.indexed == 0 and batch_num > 10:
                logger.warning(
                    "VectorIndexingService.index_all_pending — aborting after %d "
                    "batches with no successful indexing. job_id=%s",
                    batch_num,
                    job_id,
                )
                break

        result.index_size = self._store.get_index_size()
        result.duration_s = time.monotonic() - start

        logger.info(
            "VectorIndexingService.index_all_pending — completed: "
            "total=%d indexed=%d skipped=%d failed=%d "
            "index_size=%d batches=%d job_id=%s duration_s=%.3f",
            result.total,
            result.indexed,
            result.skipped,
            result.failed,
            result.index_size,
            batch_num,
            job_id,
            result.duration_s,
        )
        return result

    # ── Rebuild ───────────────────────────────────────────────────────────────

    def rebuild_index(
        self,
        db: Session,
        *,
        job_id: str | None = None,
    ) -> IndexingResult:
        """
        Safely rebuild the entire FAISS index from all READY embeddings in PostgreSQL.

        The old index is preserved until the new one is fully built and validated.
        If rebuild fails, the old index remains active.

        Strategy:
            1. Fetch all READY embeddings from PostgreSQL.
            2. Validate all vectors.
            3. Call VectorStore.rebuild_index() (atomic replacement).
            4. Update vector_index_entries for all successfully indexed embeddings.
            5. Commit.

        Args:
            db     : Active SQLAlchemy session.
            job_id : Optional tracing identifier.

        Returns:
            IndexingResult with rebuild counters.

        Raises:
            VectorRebuildError: Rebuild failed; old index preserved.
        """
        job_id = job_id or str(uuid.uuid4())
        logger.info(
            "VectorIndexingService.rebuild_index — started: job_id=%s",
            job_id,
        )
        start = time.monotonic()
        _inc("rebuild_jobs_total")

        result = IndexingResult(job_id=job_id)

        # ── 1. Load all READY embeddings ──────────────────────────────────
        # Fetch in batches to avoid loading millions of vectors at once
        all_vectors: list[list[float]] = []
        all_embedding_ids: list[str] = []
        failed_ids: list[str] = []

        batch_offset = 0
        expected_dim = self._store.get_dimension()

        while True:
            batch = (
                db.query(Embedding)
                .filter(Embedding.status == EmbeddingStatus.READY.value)
                .order_by(Embedding.created_at)
                .offset(batch_offset)
                .limit(self._batch_size)
                .all()
            )
            if not batch:
                break

            for emb in batch:
                vector = emb.get_vector()
                valid, reason = self._validate_vector_for_indexing(
                    vector, expected_dim, embedding_id=emb.id
                )
                if not valid:
                    logger.warning(
                        "VectorIndexingService.rebuild_index — skipping invalid vector: "
                        "embedding_id=%s reason=%s job_id=%s",
                        emb.id,
                        reason,
                        job_id,
                    )
                    failed_ids.append(emb.id)
                    result.failed += 1
                    continue

                all_vectors.append(vector)
                all_embedding_ids.append(emb.id)

            batch_offset += len(batch)

        result.total = batch_offset
        result.processed = len(all_vectors) + len(failed_ids)

        logger.info(
            "VectorIndexingService.rebuild_index — loaded %d valid vectors, "
            "%d invalid. Rebuilding FAISS index... job_id=%s",
            len(all_vectors),
            len(failed_ids),
            job_id,
        )

        # ── 2. Rebuild FAISS (atomic) ─────────────────────────────────────
        try:
            self._store.rebuild_index(all_vectors, all_embedding_ids)
        except VectorRebuildError:
            logger.error(
                "VectorIndexingService.rebuild_index — FAISS rebuild failed. "
                "Old index preserved. job_id=%s",
                job_id,
            )
            raise

        # ── 3. Update PostgreSQL records ──────────────────────────────────
        from app.vector_store.faiss_store import _embedding_id_to_faiss_id

        for emb_id in all_embedding_ids:
            faiss_id = _embedding_id_to_faiss_id(emb_id)
            try:
                vidx_repo.upsert_index_entry(
                    db,
                    embedding_id=emb_id,
                    faiss_id=faiss_id,
                    status=VectorIndexStatus.INDEXED.value,
                )
                result.indexed += 1
            except Exception as exc:
                logger.error(
                    "VectorIndexingService.rebuild_index — DB upsert failed for "
                    "embedding_id=%s: %s job_id=%s",
                    emb_id,
                    exc,
                    job_id,
                )
                result.failed += 1

        try:
            db.commit()
        except Exception as exc:
            db.rollback()
            logger.error(
                "VectorIndexingService.rebuild_index — DB commit failed: %s job_id=%s",
                exc,
                job_id,
            )
            raise VectorRebuildError(
                "FAISS index rebuilt successfully but PostgreSQL commit failed. "
                "Run reconciliation to restore consistency.",
                cause=exc,
            ) from exc

        result.index_size = self._store.get_index_size()
        result.duration_s = time.monotonic() - start

        logger.info(
            "VectorIndexingService.rebuild_index — completed: "
            "total=%d indexed=%d failed=%d index_size=%d job_id=%s duration_s=%.3f",
            result.total,
            result.indexed,
            result.failed,
            result.index_size,
            job_id,
            result.duration_s,
        )
        return result

    # ── Remove document vectors ───────────────────────────────────────────────

    def remove_document_vectors(
        self,
        db: Session,
        *,
        parsed_document_id: str,
        user_id: int,
        job_id: str | None = None,
    ) -> int:
        """
        Remove FAISS vectors for all embeddings belonging to a document.

        Used when a document is archived or deleted.
        Enforces user ownership.

        Args:
            db                 : Active SQLAlchemy session.
            parsed_document_id : Document to clear vectors for.
            user_id            : Authenticated owner's user ID.
            job_id             : Optional tracing identifier.

        Returns:
            Number of vectors removed from FAISS.
        """
        job_id = job_id or str(uuid.uuid4())
        logger.info(
            "VectorIndexingService.remove_document_vectors — started: "
            "parsed_document_id=%s user_id=%d job_id=%s",
            parsed_document_id,
            user_id,
            job_id,
        )

        # Fetch indexed entries for this document (ownership enforced via join)
        entries = vidx_repo.get_indexed_entries_for_document(db, parsed_document_id)

        if not entries:
            logger.info(
                "VectorIndexingService.remove_document_vectors — no indexed vectors "
                "for parsed_document_id=%s job_id=%s",
                parsed_document_id,
                job_id,
            )
            return 0

        # Validate ownership: check that all embeddings belong to user_id
        embedding_ids = [e.embedding_id for e in entries]
        embeddings = emb_repo.get_embeddings_by_document(db, parsed_document_id)
        doc_user_ids = {e.user_id for e in embeddings}
        if doc_user_ids and user_id not in doc_user_ids:
            logger.warning(
                "VectorIndexingService.remove_document_vectors — ownership check failed: "
                "user_id=%d does not own parsed_document_id=%s job_id=%s",
                user_id,
                parsed_document_id,
                job_id,
            )
            return 0

        # Remove from FAISS
        removed = self._store.remove_vectors(embedding_ids)

        # Save FAISS state
        try:
            self._store.save_index()
        except VectorStorePersistenceError as exc:
            logger.error(
                "VectorIndexingService.remove_document_vectors — FAISS save failed: "
                "%s parsed_document_id=%s job_id=%s",
                exc,
                parsed_document_id,
                job_id,
            )
            raise

        # Update DB entries
        vidx_repo.bulk_mark_removed(db, embedding_ids)
        db.commit()

        logger.info(
            "VectorIndexingService.remove_document_vectors — completed: "
            "removed=%d parsed_document_id=%s job_id=%s",
            removed,
            parsed_document_id,
            job_id,
        )
        return removed

    # ── Reconciliation ────────────────────────────────────────────────────────

    def reconcile(
        self,
        db: Session,
        *,
        job_id: str | None = None,
    ) -> ReconciliationResult:
        """
        Detect inconsistencies between PostgreSQL vector_index_entries and FAISS.

        Checks:
            - DB says INDEXED but FAISS has no vector (missing_in_faiss).
            - FAISS has a vector but no DB record exists (orphaned_in_faiss).
            - DB entries for embeddings that are no longer READY (stale_entries).

        This method REPORTS inconsistencies but does NOT auto-fix them.
        Use rebuild_index() for a full correction.

        Args:
            db     : Active SQLAlchemy session.
            job_id : Optional tracing identifier.

        Returns:
            ReconciliationResult with counts and is_consistent flag.
        """
        job_id = job_id or str(uuid.uuid4())
        logger.info(
            "VectorIndexingService.reconcile — started: job_id=%s",
            job_id,
        )
        _inc("reconciliation_jobs_total")

        result = ReconciliationResult()

        # ── 1. What PostgreSQL thinks is INDEXED ──────────────────────────
        db_indexed_ids: set[str] = vidx_repo.get_indexed_embedding_ids_set(db)
        result.db_indexed_count = len(db_indexed_ids)

        # ── 2. What FAISS actually has ────────────────────────────────────
        faiss_indexed_ids: set[str] = self._store.get_indexed_embedding_ids()
        result.faiss_vector_count = self._store.get_index_size()

        # ── 3. Compute discrepancies ──────────────────────────────────────
        missing_in_faiss = db_indexed_ids - faiss_indexed_ids
        orphaned_in_faiss = faiss_indexed_ids - db_indexed_ids

        result.missing_in_faiss = len(missing_in_faiss)
        result.orphaned_in_faiss = len(orphaned_in_faiss)

        # ── 4. Stale DB entries (embedding no longer READY) ───────────────
        if db_indexed_ids:
            stale_count = (
                db.query(Embedding)
                .filter(
                    Embedding.id.in_(list(db_indexed_ids)),
                    Embedding.status != EmbeddingStatus.READY.value,
                )
                .count()
            )
            result.stale_entries = stale_count
        else:
            result.stale_entries = 0

        result.is_consistent = (
            result.missing_in_faiss == 0
            and result.orphaned_in_faiss == 0
            and result.stale_entries == 0
        )

        if result.is_consistent:
            logger.info(
                "VectorIndexingService.reconcile — CONSISTENT: "
                "db_indexed=%d faiss_vectors=%d job_id=%s",
                result.db_indexed_count,
                result.faiss_vector_count,
                job_id,
            )
        else:
            logger.warning(
                "VectorIndexingService.reconcile — INCONSISTENT: "
                "db_indexed=%d faiss_vectors=%d "
                "missing_in_faiss=%d orphaned_in_faiss=%d stale=%d job_id=%s",
                result.db_indexed_count,
                result.faiss_vector_count,
                result.missing_in_faiss,
                result.orphaned_in_faiss,
                result.stale_entries,
                job_id,
            )

        return result

    # ── Health check ──────────────────────────────────────────────────────────

    def get_health(self) -> dict:
        """Return health status from the underlying VectorStore."""
        health = self._store.health_check()
        return health.as_dict()

    # ── Private helpers ───────────────────────────────────────────────────────

    def _index_batch_list(
        self,
        db: Session,
        candidates: list[Embedding],
        result: IndexingResult,
        *,
        job_id: str,
    ) -> None:
        """
        Index a pre-fetched list of Embedding objects into FAISS.

        Processes in self._batch_size chunks. Updates result in-place.
        Commits to PostgreSQL after each FAISS-batch.

        Args:
            db         : Active SQLAlchemy session.
            candidates : List of READY Embedding ORM objects to index.
            result     : IndexingResult to update in-place.
            job_id     : Tracing identifier for logging.
        """
        from app.vector_store.faiss_store import _embedding_id_to_faiss_id

        expected_dim = self._store.get_dimension()
        already_indexed = self._store.get_indexed_embedding_ids()

        # Process in batches of self._batch_size
        for batch_start in range(0, len(candidates), self._batch_size):
            batch = candidates[batch_start: batch_start + self._batch_size]
            batch_id = str(uuid.uuid4())

            valid_vectors: list[list[float]] = []
            valid_embedding_ids: list[str] = []
            batch_skipped = 0
            batch_failed = 0

            for emb in batch:
                result.processed += 1

                # Idempotency: skip already indexed
                if emb.id in already_indexed:
                    logger.debug(
                        "VectorIndexingService — skipping already-indexed "
                        "embedding_id=%s job_id=%s",
                        emb.id,
                        job_id,
                    )
                    result.skipped += 1
                    batch_skipped += 1
                    _inc("vectors_skipped_total")
                    continue

                # Load and validate vector
                vector = emb.get_vector()
                valid, reason = self._validate_vector_for_indexing(
                    vector, expected_dim, embedding_id=emb.id
                )
                if not valid:
                    logger.warning(
                        "VectorIndexingService — invalid vector for embedding_id=%s: "
                        "%s batch_id=%s job_id=%s",
                        emb.id,
                        reason,
                        batch_id,
                        job_id,
                    )
                    # Record failure in PostgreSQL
                    faiss_id = _embedding_id_to_faiss_id(emb.id)
                    vidx_repo.upsert_index_entry(
                        db,
                        embedding_id=emb.id,
                        faiss_id=faiss_id,
                        status=VectorIndexStatus.INDEX_FAILED.value,
                        failure_reason=reason,
                    )
                    result.failed += 1
                    batch_failed += 1
                    _inc("vectors_failed_total")
                    continue

                valid_vectors.append(vector)
                valid_embedding_ids.append(emb.id)

            if not valid_vectors:
                logger.debug(
                    "VectorIndexingService — batch_id=%s: no valid vectors to add "
                    "(skipped=%d failed=%d) job_id=%s",
                    batch_id,
                    batch_skipped,
                    batch_failed,
                    job_id,
                )
                if batch_failed > 0:
                    try:
                        db.commit()
                    except Exception as exc:
                        db.rollback()
                        logger.error(
                            "VectorIndexingService — DB commit failed for failure records: "
                            "%s job_id=%s",
                            exc,
                            job_id,
                        )
                continue

            # ── Add to FAISS ──────────────────────────────────────────────
            try:
                added_mapping = self._store.add_vectors(valid_vectors, valid_embedding_ids)
            except (VectorDimensionMismatchError, FAISSIndexError, VectorIndexingError) as exc:
                logger.error(
                    "VectorIndexingService — FAISS add_vectors failed: %s "
                    "batch_id=%s job_id=%s",
                    exc,
                    batch_id,
                    job_id,
                )
                # Mark all in this batch as failed
                for emb_id in valid_embedding_ids:
                    faiss_id = _embedding_id_to_faiss_id(emb_id)
                    vidx_repo.upsert_index_entry(
                        db,
                        embedding_id=emb_id,
                        faiss_id=faiss_id,
                        status=VectorIndexStatus.INDEX_FAILED.value,
                        failure_reason=str(exc)[:500],
                    )
                    result.failed += 1
                    _inc("vectors_failed_total")
                try:
                    db.commit()
                except Exception:
                    db.rollback()
                continue

            # ── Persist FAISS to disk ─────────────────────────────────────
            try:
                self._store.save_index()
            except VectorStorePersistenceError as exc:
                logger.error(
                    "VectorIndexingService — FAISS save failed after batch: %s "
                    "batch_id=%s job_id=%s",
                    exc,
                    batch_id,
                    job_id,
                )
                # Vectors are in FAISS memory but not durable yet
                # Mark as failed so next run retries
                for emb_id in added_mapping.keys():
                    faiss_id = added_mapping[emb_id]
                    vidx_repo.upsert_index_entry(
                        db,
                        embedding_id=emb_id,
                        faiss_id=faiss_id,
                        status=VectorIndexStatus.INDEX_FAILED.value,
                        failure_reason=f"FAISS persistence failed: {str(exc)[:400]}",
                    )
                    result.failed += 1
                try:
                    db.commit()
                except Exception:
                    db.rollback()
                continue

            # ── Update PostgreSQL ─────────────────────────────────────────
            batch_indexed = 0
            for emb_id, faiss_id in added_mapping.items():
                try:
                    vidx_repo.upsert_index_entry(
                        db,
                        embedding_id=emb_id,
                        faiss_id=faiss_id,
                        status=VectorIndexStatus.INDEXED.value,
                    )
                    batch_indexed += 1
                    _inc("vectors_indexed_total")
                except Exception as exc:
                    logger.error(
                        "VectorIndexingService — DB upsert failed for embedding_id=%s: "
                        "%s batch_id=%s job_id=%s",
                        emb_id,
                        exc,
                        batch_id,
                        job_id,
                    )
                    result.failed += 1
                    _inc("vectors_failed_total")

            try:
                db.commit()
            except Exception as exc:
                db.rollback()
                logger.error(
                    "VectorIndexingService — DB commit failed for batch: %s "
                    "batch_id=%s job_id=%s",
                    exc,
                    batch_id,
                    job_id,
                )
                result.failed += batch_indexed
                result.indexed -= batch_indexed if batch_indexed <= result.indexed else 0
                continue

            result.indexed += batch_indexed
            # Update already_indexed set for next batch's idempotency check
            already_indexed.update(added_mapping.keys())

            logger.info(
                "VectorIndexingService — batch completed: "
                "indexed=%d skipped=%d failed=%d "
                "batch_id=%s job_id=%s",
                batch_indexed,
                batch_skipped,
                batch_failed + (len(valid_embedding_ids) - batch_indexed),
                batch_id,
                job_id,
            )

    @staticmethod
    def _validate_vector_for_indexing(
        vector: list[float] | None,
        expected_dim: int,
        *,
        embedding_id: str,
    ) -> tuple[bool, str]:
        """
        Validate a vector before adding it to FAISS.

        Args:
            vector       : The float vector to validate (may be None).
            expected_dim : Expected number of elements.
            embedding_id : For log context (never logs the vector itself).

        Returns:
            (True, "") if valid.
            (False, reason_string) if invalid.
        """
        if vector is None:
            return False, "Vector is None (embedding may be PENDING/FAILED)"

        if len(vector) == 0:
            return False, "Vector is empty (length=0)"

        if len(vector) != expected_dim:
            return False, (
                f"Dimension mismatch: expected={expected_dim}, actual={len(vector)}"
            )

        try:
            arr = np.array(vector, dtype=np.float32)
        except (ValueError, TypeError) as exc:
            return False, f"Cannot convert to float32: {exc}"

        if not np.isfinite(arr).all():
            nan_count = int(np.isnan(arr).sum())
            inf_count = int(np.isinf(arr).sum())
            return False, f"Vector contains NaN={nan_count} Inf={inf_count}"

        return True, ""
