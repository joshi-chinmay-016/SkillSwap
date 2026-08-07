"""
ChunkService — Chunk storage orchestration (Day 68 Part A2).

Responsibilities:
    - Persist generated chunks (via ChunkingService + ChunkRepository).
    - Validate ownership before every operation.
    - Archive previous chunk sets on rechunking.
    - Prevent duplicate bulk inserts.
    - Collect and expose chunk metadata.
    - Log all operations.

Business logic belongs here.  The repository handles only persistence.

Metrics tracked (in-memory):
    - chunks_saved_total
    - chunks_archived_total
    - chunk_persistence_failures
    - bulk_insert_count
    - archive_count
"""
from __future__ import annotations

import hashlib
import logging
import time
from threading import Lock

from sqlalchemy.orm import Session

from app.models.chunk import Chunk, ChunkStatus
from app.repositories import chunk_repository as repo
from app.schemas.chunk import ChunkGenerationResult, ChunkListResponse, ChunkMetadata, ChunkSummary, ChunkDetail
from app.services.chunking_service import ChunkingService
from app.utils.chunk_integrity_validator import ChunkIntegrityError, validate_chunk_set
from parsers.chunking.chunk_strategy import ChunkData

logger = logging.getLogger(__name__)

# ── In-memory metrics ─────────────────────────────────────────────────────────

_METRICS_LOCK = Lock()
_METRICS: dict[str, float] = {
    "chunks_saved_total": 0,
    "chunks_archived_total": 0,
    "chunk_persistence_failures": 0,
    "bulk_insert_count": 0,
    "archive_count": 0,
    "persistence_latency_ms_total": 0.0,
}


def _record_save(count: int, duration_ms: float) -> None:
    with _METRICS_LOCK:
        _METRICS["chunks_saved_total"] += count
        _METRICS["bulk_insert_count"] += 1
        _METRICS["persistence_latency_ms_total"] += duration_ms


def _record_archive(count: int) -> None:
    with _METRICS_LOCK:
        _METRICS["chunks_archived_total"] += count
        _METRICS["archive_count"] += 1


def _record_failure() -> None:
    with _METRICS_LOCK:
        _METRICS["chunk_persistence_failures"] += 1


class ChunkService:
    """
    Orchestrates chunk persistence, retrieval, versioning, and lifecycle.

    All public methods:
        - Validate user ownership.
        - Use ChunkRepository for persistence.
        - Never expose raw SQL or ORM internals to callers.
    """

    # ── Generate & Save ───────────────────────────────────────────────────────

    @classmethod
    def save_chunks(
        cls,
        db: Session,
        *,
        document_id: str,
        user_id: int,
        chunk_size: int | None = None,
        chunk_overlap: int | None = None,
        strategy_name: str | None = None,
    ) -> ChunkGenerationResult:
        """
        Generate chunks from a ParsedDocument and persist them.

        Flow:
            1. Validate ownership.
            2. Generate chunks via ChunkingService.
            3. Deduplicate against any existing PENDING chunks.
            4. Run integrity validation.
            5. Bulk insert.
            6. Commit.

        Args:
            db            : Active SQLAlchemy session.
            document_id   : Parent Document UUID.
            user_id       : Authenticated user ID.
            chunk_size    : Override default chunk size.
            chunk_overlap : Override default overlap.
            strategy_name : Force a specific strategy name.

        Returns:
            ChunkGenerationResult with summary metadata.
        """
        from app.core.config import settings
        from app.repositories.parsed_document_repository import get_parsed_document

        resolved_size = chunk_size or settings.CHUNK_SIZE
        resolved_overlap = chunk_overlap or settings.CHUNK_OVERLAP

        logger.info(
            "ChunkService.save_chunks — document_id=%s user_id=%d",
            document_id,
            user_id,
        )

        # Step 1: resolve parsed_document_id
        parsed = get_parsed_document(db, document_id)
        if not parsed:
            raise ValueError(
                f"No ParsedDocument found for document_id={document_id}."
            )
        parsed_document_id: str = parsed.id

        try:
            # Step 2: generate chunks (ChunkingService handles ownership + validation)
            chunk_data_list: list[ChunkData] = ChunkingService.generate_chunks(
                db,
                document_id=document_id,
                user_id=user_id,
                chunk_size=resolved_size,
                chunk_overlap=resolved_overlap,
                strategy_name=strategy_name,
            )

            if not chunk_data_list:
                logger.warning(
                    "ChunkService.save_chunks — no chunks generated for document_id=%s",
                    document_id,
                )
                db.commit()
                return ChunkGenerationResult(
                    parsed_document_id=parsed_document_id,
                    chunk_count=0,
                    strategy="recursive",
                    strategy_version="1.0.0",
                    chunk_size=resolved_size,
                    overlap_size=resolved_overlap,
                    status="READY",
                    message="Document has no content to chunk.",
                )

            # Step 3: dedup — skip if identical chunk set already READY
            existing_count = repo.get_chunk_count(
                db, parsed_document_id, status_filter=ChunkStatus.READY.value
            )
            if existing_count > 0:
                logger.info(
                    "ChunkService.save_chunks — %d READY chunks already exist for %s, "
                    "skipping (use regenerate_chunks to replace)",
                    existing_count,
                    parsed_document_id,
                )
                first = chunk_data_list[0]
                return ChunkGenerationResult(
                    parsed_document_id=parsed_document_id,
                    chunk_count=existing_count,
                    strategy=first.strategy,
                    strategy_version=first.strategy_version,
                    chunk_size=resolved_size,
                    overlap_size=resolved_overlap,
                    status="READY",
                    message=f"Chunks already exist ({existing_count} READY). "
                            "Use regenerate_chunks() to replace.",
                )

            # Step 4: integrity validation
            errors = validate_chunk_set(chunk_data_list)
            if errors:
                _record_failure()
                logger.error(
                    "ChunkService — integrity validation failed: %d error(s) for %s",
                    len(errors),
                    parsed_document_id,
                )
                raise ChunkIntegrityError(errors)

            # Step 5: bulk insert
            start_ts = time.monotonic()
            repo.bulk_create_chunks(
                db,
                parsed_document_id=parsed_document_id,
                user_id=user_id,
                chunk_data_list=chunk_data_list,
                status=ChunkStatus.READY.value,
            )
            duration_ms = (time.monotonic() - start_ts) * 1000

            # Step 6: commit
            db.commit()
            _record_save(len(chunk_data_list), duration_ms)

            first = chunk_data_list[0]
            logger.info(
                "ChunkService.save_chunks — persisted %d chunks (%.1f ms) for %s",
                len(chunk_data_list),
                duration_ms,
                parsed_document_id,
            )

            return ChunkGenerationResult(
                parsed_document_id=parsed_document_id,
                chunk_count=len(chunk_data_list),
                strategy=first.strategy,
                strategy_version=first.strategy_version,
                chunk_size=resolved_size,
                overlap_size=resolved_overlap,
                status="READY",
                message=f"Successfully generated {len(chunk_data_list)} chunks.",
            )

        except (ValueError, ChunkIntegrityError):
            db.rollback()
            _record_failure()
            raise
        except Exception as exc:
            db.rollback()
            _record_failure()
            logger.exception(
                "ChunkService.save_chunks — unexpected failure for %s: %s",
                document_id,
                exc,
            )
            raise

    # ── Regenerate (Rechunk) ──────────────────────────────────────────────────

    @classmethod
    def regenerate_chunks(
        cls,
        db: Session,
        *,
        document_id: str,
        user_id: int,
        chunk_size: int | None = None,
        chunk_overlap: int | None = None,
        strategy_name: str | None = None,
    ) -> ChunkGenerationResult:
        """
        Archive existing READY chunks and generate a fresh chunk set.

        Flow:
            1. Archive existing READY chunks → ARCHIVED.
            2. Generate new chunks.
            3. Bulk insert new chunks.
            4. Commit.

        Args:
            db            : Active SQLAlchemy session.
            document_id   : Parent Document UUID.
            user_id       : Authenticated user ID.
            chunk_size    : Override default chunk size.
            chunk_overlap : Override default overlap.
            strategy_name : Force a specific strategy name.

        Returns:
            ChunkGenerationResult for the new chunk set.
        """
        from app.core.config import settings
        from app.repositories.parsed_document_repository import get_parsed_document

        resolved_size = chunk_size or settings.CHUNK_SIZE
        resolved_overlap = chunk_overlap or settings.CHUNK_OVERLAP

        logger.info(
            "ChunkService.regenerate_chunks — document_id=%s user_id=%d",
            document_id,
            user_id,
        )

        parsed = get_parsed_document(db, document_id)
        if not parsed:
            raise ValueError(
                f"No ParsedDocument found for document_id={document_id}."
            )
        parsed_document_id: str = parsed.id

        try:
            # Step 1: archive existing READY chunks
            archived_count = repo.archive_chunks_for_document(
                db, parsed_document_id, from_status=ChunkStatus.READY.value
            )
            if archived_count > 0:
                _record_archive(archived_count)
                logger.info(
                    "ChunkService.regenerate_chunks — archived %d chunks for %s",
                    archived_count,
                    parsed_document_id,
                )

            # Steps 2-4: generate and persist (reuse save_chunks logic but skip dedup)
            chunk_data_list: list[ChunkData] = ChunkingService.generate_chunks(
                db,
                document_id=document_id,
                user_id=user_id,
                chunk_size=resolved_size,
                chunk_overlap=resolved_overlap,
                strategy_name=strategy_name,
            )

            errors = validate_chunk_set(chunk_data_list)
            if errors:
                _record_failure()
                raise ChunkIntegrityError(errors)

            start_ts = time.monotonic()
            repo.bulk_create_chunks(
                db,
                parsed_document_id=parsed_document_id,
                user_id=user_id,
                chunk_data_list=chunk_data_list,
                status=ChunkStatus.READY.value,
            )
            duration_ms = (time.monotonic() - start_ts) * 1000

            db.commit()
            _record_save(len(chunk_data_list), duration_ms)

            first = chunk_data_list[0] if chunk_data_list else None
            logger.info(
                "ChunkService.regenerate_chunks — persisted %d new chunks for %s",
                len(chunk_data_list),
                parsed_document_id,
            )

            return ChunkGenerationResult(
                parsed_document_id=parsed_document_id,
                chunk_count=len(chunk_data_list),
                strategy=first.strategy if first else "recursive",
                strategy_version=first.strategy_version if first else "1.0.0",
                chunk_size=resolved_size,
                overlap_size=resolved_overlap,
                status="READY",
                message=(
                    f"Archived {archived_count} old chunk(s). "
                    f"Generated {len(chunk_data_list)} new chunk(s)."
                ),
            )

        except (ValueError, ChunkIntegrityError):
            db.rollback()
            _record_failure()
            raise
        except Exception as exc:
            db.rollback()
            _record_failure()
            logger.exception(
                "ChunkService.regenerate_chunks — unexpected failure for %s: %s",
                document_id,
                exc,
            )
            raise

    # ── Retrieve ──────────────────────────────────────────────────────────────

    @classmethod
    def get_chunks(
        cls,
        db: Session,
        *,
        document_id: str,
        user_id: int,
        page: int = 1,
        page_size: int = 100,
        status_filter: str | None = None,
    ) -> ChunkListResponse:
        """
        Retrieve a paginated list of chunks for a document.

        Args:
            db            : Active SQLAlchemy session.
            document_id   : Parent Document UUID.
            user_id       : Authenticated user ID (ownership check).
            page          : 1-indexed page number.
            page_size     : Records per page.
            status_filter : Optional ChunkStatus filter.

        Returns:
            ChunkListResponse with paginated chunks.
        """
        from app.repositories.parsed_document_repository import get_parsed_document
        from app.models.document import Document

        cls._assert_document_ownership(db, document_id, user_id)

        parsed = get_parsed_document(db, document_id)
        if not parsed:
            raise ValueError(f"No ParsedDocument found for document_id={document_id}.")

        chunks, total = repo.list_chunks_by_document(
            db,
            parsed.id,
            status_filter=status_filter,
            page=page,
            page_size=page_size,
        )

        return ChunkListResponse(
            parsed_document_id=parsed.id,
            chunks=[ChunkDetail.model_validate(c) for c in chunks],
            total=total,
            page=page,
            page_size=page_size,
            has_next=(page * page_size) < total,
            has_previous=page > 1,
        )

    @classmethod
    def count_chunks(
        cls,
        db: Session,
        *,
        document_id: str,
        user_id: int,
        status_filter: str | None = None,
    ) -> int:
        """Return chunk count for a document."""
        from app.repositories.parsed_document_repository import get_parsed_document

        cls._assert_document_ownership(db, document_id, user_id)
        parsed = get_parsed_document(db, document_id)
        if not parsed:
            return 0
        return repo.get_chunk_count(db, parsed.id, status_filter=status_filter)

    @classmethod
    def get_chunk_metadata(
        cls,
        db: Session,
        *,
        document_id: str,
        user_id: int,
    ) -> ChunkMetadata:
        """
        Return aggregate metadata for a document's READY chunk set.

        Args:
            db          : Active SQLAlchemy session.
            document_id : Parent Document UUID.
            user_id     : Authenticated user ID.

        Returns:
            ChunkMetadata with totals, averages, and strategy info.
        """
        from app.core.config import settings
        from app.repositories.parsed_document_repository import get_parsed_document

        cls._assert_document_ownership(db, document_id, user_id)
        parsed = get_parsed_document(db, document_id)
        if not parsed:
            raise ValueError(f"No ParsedDocument found for document_id={document_id}.")

        ready_chunks = repo.get_ready_chunks(db, parsed.id)
        total = len(ready_chunks)

        if total == 0:
            return ChunkMetadata(
                parsed_document_id=parsed.id,
                total_chunks=0,
                strategy=settings.CHUNK_STRATEGY,
                strategy_version=settings.CHUNK_STRATEGY_VERSION,
                chunk_size=settings.CHUNK_SIZE,
                overlap_size=settings.CHUNK_OVERLAP,
                total_chars=0,
                total_estimated_tokens=0,
                average_chunk_size=0.0,
                average_chunk_tokens=0.0,
            )

        total_chars = sum(len(c.chunk_text or "") for c in ready_chunks)
        total_tokens = sum(c.estimated_tokens for c in ready_chunks)
        first = ready_chunks[0]

        status_counts: dict[str, int] = {}
        for c in ready_chunks:
            status_counts[c.status] = status_counts.get(c.status, 0) + 1

        return ChunkMetadata(
            parsed_document_id=parsed.id,
            total_chunks=total,
            strategy=first.strategy,
            strategy_version=first.strategy_version,
            chunk_size=first.chunk_size,
            overlap_size=first.overlap_size,
            total_chars=total_chars,
            total_estimated_tokens=total_tokens,
            average_chunk_size=total_chars / total,
            average_chunk_tokens=total_tokens / total,
            status_counts=status_counts,
        )

    # ── Archive ───────────────────────────────────────────────────────────────

    @classmethod
    def archive_chunks(
        cls,
        db: Session,
        *,
        document_id: str,
        user_id: int,
    ) -> int:
        """
        Archive all READY chunks for a document (without regenerating).

        Args:
            db          : Active SQLAlchemy session.
            document_id : Parent Document UUID.
            user_id     : Authenticated user ID.

        Returns:
            Number of chunks archived.
        """
        from app.repositories.parsed_document_repository import get_parsed_document

        cls._assert_document_ownership(db, document_id, user_id)
        parsed = get_parsed_document(db, document_id)
        if not parsed:
            return 0

        count = repo.archive_chunks_for_document(db, parsed.id)
        db.commit()
        _record_archive(count)

        logger.info(
            "ChunkService.archive_chunks — archived %d chunks for %s",
            count,
            parsed.id,
        )
        return count

    # ── Metrics ───────────────────────────────────────────────────────────────

    @staticmethod
    def get_metrics() -> dict:
        """Return current in-memory metrics snapshot."""
        with _METRICS_LOCK:
            return dict(_METRICS)

    # ── Private helpers ───────────────────────────────────────────────────────

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
