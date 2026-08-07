"""
ChunkingService — Orchestrates chunk generation from ParsedDocuments (Day 68 Part A1).

Responsibilities:
    1. Load ParsedDocument from the repository.
    2. Validate it is READY and belongs to the requesting user.
    3. Select a chunking strategy via ChunkFactory.
    4. Run the chunking pipeline.
    5. Validate produced chunks.
    6. Return ChunkData list to the caller (ChunkService handles persistence).

This service has NO database write operations — it only reads ParsedDocuments.
Persistence is delegated to ChunkService (Part A2) to maintain separation.

Metrics tracked (in-memory counters, reset on restart):
    - chunk_generation_total
    - chunk_generation_failures
    - chunk_count_total
    - chunk_generation_duration_ms_total
"""
from __future__ import annotations

import logging
import time
from threading import Lock
from typing import Optional

from sqlalchemy.orm import Session

from app.repositories.parsed_document_repository import get_parsed_document
from app.utils.chunk_validator import ChunkValidationError, validate_chunks
from app.utils.token_estimator import estimate_tokens
from parsers.chunking.chunk_factory import ChunkFactory
from parsers.chunking.chunk_strategy import ChunkData

logger = logging.getLogger(__name__)

# ── In-memory metrics ─────────────────────────────────────────────────────────

_METRICS_LOCK = Lock()
_METRICS: dict[str, float] = {
    "chunk_generation_total": 0,
    "chunk_generation_failures": 0,
    "chunk_count_total": 0,
    "chunk_generation_duration_ms_total": 0.0,
    "strategy_usage": {},  # type: ignore[dict-item]
}


def _record_success(strategy: str, count: int, duration_ms: float) -> None:
    with _METRICS_LOCK:
        _METRICS["chunk_generation_total"] += 1
        _METRICS["chunk_count_total"] += count
        _METRICS["chunk_generation_duration_ms_total"] += duration_ms
        usage = _METRICS.setdefault("strategy_usage", {})
        usage[strategy] = usage.get(strategy, 0) + 1  # type: ignore[index]


def _record_failure() -> None:
    with _METRICS_LOCK:
        _METRICS["chunk_generation_failures"] += 1


class ChunkingService:
    """
    Orchestrates text chunk generation from a ParsedDocument.

    Usage::

        chunks = ChunkingService.generate_chunks(
            db=db,
            document_id="uuid",
            user_id=42,
        )
    """

    # ── Public API ────────────────────────────────────────────────────────────

    @classmethod
    def generate_chunks(
        cls,
        db: Session,
        *,
        document_id: str,
        user_id: int,
        chunk_size: Optional[int] = None,
        chunk_overlap: Optional[int] = None,
        strategy_name: Optional[str] = None,
    ) -> list[ChunkData]:
        """
        Generate semantic chunks for the given document.

        Args:
            db            : Active SQLAlchemy session (read-only).
            document_id   : ID of the parent Document record.
            user_id       : ID of the requesting user (ownership check).
            chunk_size    : Override default chunk size (chars).
            chunk_overlap : Override default overlap (chars).
            strategy_name : Force a specific strategy name (optional).

        Returns:
            Ordered list of ChunkData objects ready for persistence.

        Raises:
            ValueError: If document is not found, not parsed, or not owned by user.
            ChunkValidationError: If generated chunks fail validation.
        """
        from app.core.config import settings

        resolved_size = chunk_size or settings.CHUNK_SIZE
        resolved_overlap = chunk_overlap or settings.CHUNK_OVERLAP

        logger.info(
            "ChunkingService.generate_chunks — document_id=%s user_id=%d "
            "chunk_size=%d overlap=%d",
            document_id,
            user_id,
            resolved_size,
            resolved_overlap,
        )

        # Step 1: Fetch and validate ParsedDocument
        parsed = get_parsed_document(db, document_id)
        cls._assert_parsed_document_ready(parsed, document_id, user_id, db)

        text: str = parsed.text_content or ""  # type: ignore[union-attr]

        if not text.strip():
            logger.warning(
                "ChunkingService — document_id=%s has empty text_content, "
                "returning empty chunk list",
                document_id,
            )
            return []

        # Step 2: Determine document type for strategy selection
        doc_type = cls._get_document_type(db, document_id)

        # Step 3: Select strategy
        if strategy_name:
            strategy = ChunkFactory.get_strategy(strategy_name)
        else:
            strategy = ChunkFactory.get_strategy(doc_type)

        logger.info(
            "ChunkingService — selected strategy '%s' v%s for doc_type='%s'",
            strategy.name,
            strategy.version,
            doc_type,
        )

        # Step 4: Generate chunks
        start_ts = time.monotonic()
        try:
            chunks = strategy.chunk(
                text,
                chunk_size=resolved_size,
                chunk_overlap=resolved_overlap,
                document_type=doc_type,
            )
        except Exception as exc:
            _record_failure()
            logger.exception(
                "ChunkingService — chunk generation failed for document_id=%s: %s",
                document_id,
                exc,
            )
            raise

        duration_ms = (time.monotonic() - start_ts) * 1000

        # Step 5: Validate chunks
        errors = validate_chunks(chunks)
        if errors:
            _record_failure()
            logger.error(
                "ChunkingService — validation failed for document_id=%s: %d error(s)",
                document_id,
                len(errors),
            )
            raise ChunkValidationError(errors)

        _record_success(strategy.name, len(chunks), duration_ms)

        logger.info(
            "ChunkingService — generated %d chunks in %.1f ms for document_id=%s",
            len(chunks),
            duration_ms,
            document_id,
        )
        return chunks

    @classmethod
    def estimate_tokens(cls, text: str) -> int:
        """
        Estimate the approximate token count for the given text.

        Args:
            text: Any plain-text string.

        Returns:
            Non-negative integer estimate.
        """
        return estimate_tokens(text)

    @classmethod
    def validate_chunks(
        cls,
        chunks: list[ChunkData],
    ) -> list[str]:
        """
        Validate a list of ChunkData objects without persistence.

        Args:
            chunks: ChunkData list to validate.

        Returns:
            List of error strings.  Empty = valid.
        """
        return validate_chunks(chunks)

    @staticmethod
    def get_metrics() -> dict:
        """Return current in-memory metrics snapshot."""
        with _METRICS_LOCK:
            return dict(_METRICS)

    # ── Private helpers ───────────────────────────────────────────────────────

    @staticmethod
    def _assert_parsed_document_ready(
        parsed: object,
        document_id: str,
        user_id: int,
        db: Session,
    ) -> None:
        """Raise ValueError if ParsedDocument is missing or not ready."""
        from app.models.document import Document
        from app.models.parsed_document import ParsedDocumentStatus

        if parsed is None:
            raise ValueError(
                f"ParsedDocument not found for document_id={document_id}. "
                "The document must be successfully parsed before chunking."
            )

        # Ownership: fetch parent Document and check user_id
        document = db.query(Document).filter_by(id=document_id).first()
        if not document:
            raise ValueError(f"Document {document_id} not found.")
        if document.user_id != user_id:
            raise ValueError(
                f"Document {document_id} does not belong to user {user_id}."
            )

        if parsed.status != ParsedDocumentStatus.READY.value:  # type: ignore[union-attr]
            raise ValueError(
                f"ParsedDocument for document_id={document_id} is not READY "
                f"(status={parsed.status}). Chunking requires a successfully "  # type: ignore[union-attr]
                "parsed document."
            )

    @staticmethod
    def _get_document_type(db: Session, document_id: str) -> str:
        """Return the lowercase file extension of the parent Document."""
        from app.models.document import Document

        document = db.query(Document).filter_by(id=document_id).first()
        if document and document.file_extension:
            return document.file_extension.lower()
        return "txt"
