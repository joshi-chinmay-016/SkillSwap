"""
RetrievalService — Retrieval orchestration layer (Day 71).

Responsibilities:
    1. Validate the RetrievalRequest (query, top_k, threshold, document_id).
    2. Generate a query embedding using the existing embedding provider.
    3. Validate the query embedding dimension against the FAISS index.
    4. Delegate to FAISSRetriever for vector search + metadata resolution.
    5. Return a typed RetrievalResponse with per-stage timing metrics.

Design:
    - Uses existing EmbeddingProvider from Day 69 (no new provider).
    - Uses existing FAISSVectorStore.from_settings() from Day 70.
    - Configuration via app.core.config.settings (no hardcoded values).
    - Factory method mirrors EmbeddingService.create() pattern.

Security:
    - Never logs raw query text (may contain sensitive user content).
    - Never logs embedding vectors.
    - Never exposes FAISS IDs or filesystem paths to callers.
    - user_id is always passed to FAISSRetriever for authorization.
"""
from __future__ import annotations

import logging
import time
import uuid
from typing import Optional

from sqlalchemy.orm import Session

from app.core.config import settings
from app.retrieval.faiss_retriever import FAISSRetriever
from app.retrieval.retrieval_exceptions import (
    InvalidRetrievalRequestError,
    QueryEmbeddingError,
    RetrievalUnavailableError,
    VectorStoreSearchError,
)
from app.retrieval.retrieval_models import (
    RetrievalRequest,
    RetrievedChunk,
    RetrievalResponse,
)
from app.retrieval.retriever import Retriever
from app.vector_store.exceptions import VectorDimensionMismatchError

logger = logging.getLogger(__name__)

_UUID_LEN = 36  # 8-4-4-4-12 format


class RetrievalService:
    """
    Orchestrates the full retrieval pipeline from user query to ranked chunks.

    Usage::

        service = RetrievalService.create()
        response = service.retrieve(
            db,
            request=RetrievalRequest(query="What is dependency injection?", top_k=5),
            user_id=current_user.id,
        )
        for chunk in response.results:
            print(chunk.rank, chunk.score, chunk.content[:80])
    """

    def __init__(
        self,
        retriever: Retriever,
        embedding_provider,  # EmbeddingProvider — typed loosely to avoid circular import
        *,
        default_top_k: int,
        max_top_k: int,
        default_threshold: float,
        max_query_length: int,
    ) -> None:
        self._retriever = retriever
        self._provider = embedding_provider
        self._default_top_k = default_top_k
        self._max_top_k = max_top_k
        self._default_threshold = default_threshold
        self._max_query_length = max_query_length

    # ── Factory ───────────────────────────────────────────────────────────────

    @classmethod
    def create(cls) -> "RetrievalService":
        """
        Construct a RetrievalService from application settings.

        Initializes the FAISS vector store and embedding provider using the
        same configuration as the Day 70 indexing pipeline.

        Returns:
            Ready-to-use RetrievalService.

        Raises:
            RetrievalUnavailableError: Vector store cannot be initialized.
        """
        from app.embeddings.providers.gemini_embedding_provider import (
            GeminiEmbeddingProvider,
        )
        from app.vector_store.faiss_store import FAISSVectorStore
        from app.vector_store.exceptions import (
            VectorStoreInitializationError,
            VectorStorePersistenceError,
        )

        # ── Vector store ──────────────────────────────────────────────────
        try:
            store = FAISSVectorStore.from_settings()
            store.initialize_index()
        except (VectorStoreInitializationError, VectorStorePersistenceError) as exc:
            raise RetrievalUnavailableError(
                "FAISS vector store could not be initialized for retrieval.",
                cause=exc,
            ) from exc

        candidate_multiplier: int = getattr(
            settings, "RETRIEVAL_CANDIDATE_MULTIPLIER", 4
        )
        retriever = FAISSRetriever(store, candidate_multiplier=candidate_multiplier)

        # ── Embedding provider ────────────────────────────────────────────
        provider = GeminiEmbeddingProvider()

        return cls(
            retriever=retriever,
            embedding_provider=provider,
            default_top_k=getattr(settings, "RETRIEVAL_DEFAULT_TOP_K", 5),
            max_top_k=getattr(settings, "RETRIEVAL_MAX_TOP_K", 20),
            default_threshold=getattr(settings, "RETRIEVAL_SIMILARITY_THRESHOLD", 0.0),
            max_query_length=getattr(settings, "RETRIEVAL_MAX_QUERY_LENGTH", 2000),
        )

    # ── Public interface ───────────────────────────────────────────────────────

    def retrieve(
        self,
        db: Session,
        *,
        request: RetrievalRequest,
        user_id: int,
    ) -> RetrievalResponse:
        """
        Execute the full retrieval pipeline and return ranked chunks.

        Args:
            db      : Active SQLAlchemy session (read-only usage by retrieval layer).
            request : Validated retrieval request.
            user_id : Authenticated user performing the query.

        Returns:
            RetrievalResponse with ordered results and per-stage timings.

        Raises:
            InvalidRetrievalRequestError : Bad input rejected before any external call.
            QueryEmbeddingError          : Query embedding failed.
            VectorStoreSearchError       : FAISS search or dimension mismatch.
            MetadataResolutionError      : PostgreSQL lookup failed.
            RetrievalUnavailableError    : Infrastructure not ready.
        """
        request_id = str(uuid.uuid4())[:8]
        t_start = time.perf_counter()

        # ── Step 1: Validate request ──────────────────────────────────────────
        top_k, threshold = self._validate_request(request)

        logger.info(
            "RetrievalService.retrieve — request_id=%s user_id=%d "
            "top_k=%d threshold=%.3f document_scoped=%s",
            request_id, user_id, top_k, threshold,
            request.document_id is not None,
        )

        # ── Step 2: Generate query embedding ─────────────────────────────────
        t_emb_start = time.perf_counter()
        try:
            query_vector: list[float] = self._provider.generate_embedding(request.query)
        except Exception as exc:
            raise QueryEmbeddingError(
                "Failed to generate query embedding.",
                cause=exc,
            ) from exc
        embedding_ms = (time.perf_counter() - t_emb_start) * 1000

        # ── Step 3: Validate query vector dimension ───────────────────────────
        try:
            index_dim = self._retriever._store.get_dimension()  # noqa: SLF001
        except Exception:
            index_dim = None

        if index_dim is not None and len(query_vector) != index_dim:
            raise VectorStoreSearchError(
                f"Query embedding dimension {len(query_vector)} does not match "
                f"FAISS index dimension {index_dim}. "
                "Ensure the query uses the same embedding model as indexed documents."
            )

        # ── Step 4: FAISS search + filtering ─────────────────────────────────
        t_faiss_start = time.perf_counter()
        results: list[RetrievedChunk] = self._retriever.search(
            db,
            query_vector=query_vector,
            top_k=top_k,
            user_id=user_id,
            similarity_threshold=threshold,
            document_id=request.document_id,
        )
        faiss_ms = (time.perf_counter() - t_faiss_start) * 1000

        # db_ms is embedded inside retriever.search; we estimate total minus embedding
        total_ms = (time.perf_counter() - t_start) * 1000
        db_ms = max(0.0, total_ms - embedding_ms - faiss_ms)

        logger.info(
            "RetrievalService.retrieve — request_id=%s returned=%d "
            "total_ms=%.1f embedding_ms=%.1f faiss_ms=%.1f db_ms=%.1f",
            request_id, len(results), total_ms, embedding_ms, faiss_ms, db_ms,
        )

        return RetrievalResponse(
            results=results,
            total=len(results),
            query_duration_ms=round(total_ms, 2),
            embedding_ms=round(embedding_ms, 2),
            faiss_ms=round(faiss_ms, 2),
            db_ms=round(db_ms, 2),
        )

    # ── Private helpers ────────────────────────────────────────────────────────

    def _validate_request(
        self, request: RetrievalRequest
    ) -> tuple[int, float]:
        """
        Validate the retrieval request and return (resolved_top_k, resolved_threshold).

        Raises:
            InvalidRetrievalRequestError: Any validation failure.
        """
        # Query validation
        if not request.query or not request.query.strip():
            raise InvalidRetrievalRequestError(
                "Query must not be empty or whitespace-only."
            )
        if len(request.query) > self._max_query_length:
            raise InvalidRetrievalRequestError(
                f"Query exceeds maximum length of {self._max_query_length} characters."
            )

        # top_k validation
        top_k = request.top_k if request.top_k is not None else self._default_top_k
        if top_k < 1:
            raise InvalidRetrievalRequestError(
                f"top_k must be >= 1, got {top_k}."
            )
        if top_k > self._max_top_k:
            raise InvalidRetrievalRequestError(
                f"top_k must be <= {self._max_top_k}, got {top_k}."
            )

        # threshold validation
        threshold = (
            request.similarity_threshold
            if request.similarity_threshold is not None
            else self._default_threshold
        )
        if not (0.0 <= threshold <= 1.0):
            raise InvalidRetrievalRequestError(
                f"similarity_threshold must be between 0.0 and 1.0, got {threshold}."
            )

        # document_id format validation (basic UUID length check)
        if request.document_id is not None:
            doc_id = request.document_id.strip()
            if len(doc_id) != _UUID_LEN:
                raise InvalidRetrievalRequestError(
                    f"document_id must be a valid UUID (36 characters), "
                    f"got {len(doc_id)} characters."
                )
            request.document_id = doc_id

        return top_k, threshold

    def get_metrics(
        self,
        db: Session,
        *,
        user_id: int,
    ):
        """
        Delegate retrieval metric computation to the retrieval repository.
        """
        from app.retrieval.retrieval_repository import get_retrieval_metrics
        return get_retrieval_metrics(db, user_id=user_id)

