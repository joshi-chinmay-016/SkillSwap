"""
FAISSRetriever — Production retrieval pipeline (Day 71 Parts A1 + A2).

Implements the full retrieval pipeline on top of FAISSVectorStore (Day 70):

    query_vector
        ↓
    Dimension validation
        ↓
    Candidate overfetch (top_k × CANDIDATE_MULTIPLIER)
        ↓
    FAISS search → (faiss_id, score) pairs
        ↓
    faiss_id → embedding_id (via FAISSVectorStore.resolve_faiss_ids)
        ↓
    Batch PostgreSQL metadata resolution (single JOIN query)
        ↓
    Stale vector detection (not in DB → skip + log)
        ↓
    Authorization (embedding.user_id == caller user_id)
        ↓
    Embedding lifecycle filter (status == READY)
        ↓
    Document lifecycle filter (status not ARCHIVED)
        ↓
    Chunk lifecycle filter (status == READY)
        ↓
    Document scope filter (if document_id provided)
        ↓
    Similarity threshold filter (score >= threshold)
        ↓
    Deduplication by chunk_id (keep highest score)
        ↓
    Deterministic ordering (score desc, chunk_id asc)
        ↓
    Truncate to top_k
        ↓
    list[RetrievedChunk]

Score semantics:
    IndexFlatIP returns inner-product values.
    For L2-normalised vectors: inner-product == cosine similarity.
    Higher score = more relevant.
    Do NOT invert or negate scores.

Authorization:
    FAISS has no concept of ownership.
    Every candidate is validated against user_id before being returned.
    Stale/unauthorized candidates are logged and skipped — not raised.

Concurrency:
    IndexFlatIP is thread-safe for concurrent reads.
    resolve_faiss_ids() acquires a brief read-lock on the mapping dict.
    No mutation happens during retrieval.

Security:
    No raw vectors are exposed.
    No FAISS IDs are returned to callers.
    No filesystem paths are referenced.
"""
from __future__ import annotations

import logging
from typing import Optional

from sqlalchemy.orm import Session

from app.models.chunk import ChunkStatus
from app.models.document import DocumentStatus
from app.models.embedding import EmbeddingStatus
from app.retrieval.retrieval_exceptions import (
    MetadataResolutionError,
    RetrievalUnavailableError,
    VectorStoreSearchError,
)
from app.retrieval.retrieval_models import RetrievedChunk
from app.retrieval.retrieval_repository import get_candidate_metadata_batch
from app.retrieval.retriever import Retriever
from app.vector_store.exceptions import (
    FAISSIndexError,
    VectorDimensionMismatchError,
    VectorStoreInitializationError,
)

logger = logging.getLogger(__name__)

# Parsed-document IDs are validated via document ownership — no direct document_id
# column on chunks. The retrieval uses document_id → parsed_document_ids mapping.


class FAISSRetriever(Retriever):
    """
    FAISS-backed retrieval implementation.

    Depends on FAISSVectorStore for vector search and ID resolution.
    Depends on retrieval_repository for batch PostgreSQL metadata lookup.
    """

    def __init__(
        self,
        vector_store,   # FAISSVectorStore (typed loosely to avoid circular imports)
        *,
        candidate_multiplier: int = 4,
    ) -> None:
        """
        Args:
            vector_store         : Initialized FAISSVectorStore instance.
            candidate_multiplier : Overfetch factor. FAISS fetches top_k × multiplier
                                   candidates before post-filtering. Must be >= 1.
        """
        self._store = vector_store
        self._candidate_multiplier = max(1, candidate_multiplier)

    # ── Public interface ───────────────────────────────────────────────────────

    def search(
        self,
        db: Session,
        *,
        query_vector: list[float],
        top_k: int,
        user_id: int,
        similarity_threshold: float,
        document_id: str | None,
    ) -> list[RetrievedChunk]:
        """
        Full retrieval pipeline: FAISS → ID resolution → DB metadata → filtering → results.

        See module docstring for complete pipeline description.
        """
        # ── Step 1: Dimension validation ──────────────────────────────────────
        try:
            index_dim = self._store.get_dimension()
        except VectorStoreInitializationError as exc:
            raise RetrievalUnavailableError(
                "Vector store is not initialized. Retrieval is unavailable.",
                cause=exc,
            ) from exc

        if len(query_vector) != index_dim:
            raise VectorStoreSearchError(
                f"Query vector dimension {len(query_vector)} does not match "
                f"FAISS index dimension {index_dim}. "
                "Re-embed the query using the same model as the indexed documents.",
            )

        # ── Step 2: Candidate overfetch ────────────────────────────────────────
        # Fetch more candidates than requested to compensate for post-filtering.
        candidate_limit = top_k * self._candidate_multiplier
        index_size = self._store.get_index_size()

        if index_size == 0:
            logger.info(
                "FAISSRetriever — FAISS index is empty. Returning no results. "
                "user_id=%d top_k=%d",
                user_id, top_k,
            )
            return []

        actual_fetch = min(candidate_limit, index_size)

        # ── Step 3: FAISS search ───────────────────────────────────────────────
        try:
            raw_candidates: list[tuple[int, float]] = self._store.search(
                query_vector, actual_fetch
            )
        except VectorStoreInitializationError as exc:
            raise RetrievalUnavailableError(
                "Vector store unavailable during search.",
                cause=exc,
            ) from exc
        except VectorDimensionMismatchError as exc:
            raise VectorStoreSearchError(
                f"Dimension mismatch during FAISS search: {exc}",
                cause=exc,
            ) from exc
        except FAISSIndexError as exc:
            raise VectorStoreSearchError(
                "FAISS search failed unexpectedly.",
                cause=exc,
            ) from exc

        if not raw_candidates:
            logger.debug(
                "FAISSRetriever — FAISS returned no candidates. "
                "user_id=%d top_k=%d",
                user_id, top_k,
            )
            return []

        logger.debug(
            "FAISSRetriever — FAISS returned %d raw candidates. "
            "user_id=%d top_k=%d candidate_limit=%d",
            len(raw_candidates), user_id, top_k, candidate_limit,
        )

        # ── Step 4: faiss_id → embedding_id resolution ─────────────────────────
        faiss_ids = [fid for fid, _ in raw_candidates]
        score_by_faiss_id: dict[int, float] = {fid: sc for fid, sc in raw_candidates}

        try:
            faiss_to_emb: dict[int, str] = self._store.resolve_faiss_ids(faiss_ids)
        except Exception as exc:
            raise VectorStoreSearchError(
                "Failed to resolve FAISS vector IDs to embedding IDs.",
                cause=exc,
            ) from exc

        # Detect stale vectors (in FAISS but not in mapping)
        stale_faiss_ids = [fid for fid in faiss_ids if fid not in faiss_to_emb]
        if stale_faiss_ids:
            logger.warning(
                "FAISSRetriever — %d stale FAISS vector ID(s) could not be resolved "
                "to embedding IDs. They will be skipped. "
                "Run reconciliation to repair the index. user_id=%d",
                len(stale_faiss_ids), user_id,
            )

        if not faiss_to_emb:
            logger.info(
                "FAISSRetriever — all %d FAISS candidates were stale. "
                "Returning no results. user_id=%d",
                len(faiss_ids), user_id,
            )
            return []

        # ── Step 5: Batch PostgreSQL metadata resolution ───────────────────────
        embedding_ids = list(faiss_to_emb.values())
        try:
            metadata_map = get_candidate_metadata_batch(db, embedding_ids)
        except Exception as exc:
            raise MetadataResolutionError(
                "Failed to resolve candidate metadata from PostgreSQL.",
                cause=exc,
            ) from exc

        # ── Step 6-11: Filter pipeline ─────────────────────────────────────────
        # Resolve document_id → set of parsed_document_ids for scope filtering
        target_parsed_doc_ids: set[str] | None = None
        if document_id is not None:
            target_parsed_doc_ids = self._resolve_parsed_document_ids(db, document_id)
            if target_parsed_doc_ids is None:
                # document_id not found or not owned by user
                logger.warning(
                    "FAISSRetriever — document_id=%s not found or not owned by "
                    "user_id=%d. Returning empty results.",
                    document_id, user_id,
                )
                return []

        # score by chunk_id for deduplication (keep best score per chunk)
        best_score_by_chunk: dict[str, float] = {}
        best_candidate_by_chunk: dict[str, RetrievedChunk] = {}

        authorized_count = 0
        filtered_count = 0
        stale_db_count = 0

        for fid, score in raw_candidates:
            emb_id = faiss_to_emb.get(fid)
            if emb_id is None:
                continue  # stale FAISS vector — already logged above

            meta = metadata_map.get(emb_id)
            if meta is None:
                # embedding_id resolved from FAISS but missing from DB join result
                stale_db_count += 1
                logger.debug(
                    "FAISSRetriever — embedding_id=%s not found in DB metadata. "
                    "Skipping stale candidate.",
                    emb_id,
                )
                continue

            # Authorization check
            if meta.embedding_user_id != user_id:
                filtered_count += 1
                continue

            # Embedding lifecycle
            if meta.embedding_status != EmbeddingStatus.READY.value:
                filtered_count += 1
                logger.debug(
                    "FAISSRetriever — skipping embedding_id=%s: status=%s (not READY)",
                    emb_id, meta.embedding_status,
                )
                continue

            # Document lifecycle — exclude archived/failed documents
            if meta.document_status == DocumentStatus.ARCHIVED.value:
                filtered_count += 1
                continue

            # Chunk lifecycle
            if meta.chunk_status != ChunkStatus.READY.value:
                filtered_count += 1
                continue

            # Document scope filter
            if target_parsed_doc_ids is not None:
                if meta.parsed_document_id not in target_parsed_doc_ids:
                    filtered_count += 1
                    continue

            # Similarity threshold (score >= threshold, higher is better)
            if score < similarity_threshold:
                filtered_count += 1
                continue

            authorized_count += 1

            # Deduplication: keep best-scored occurrence of each chunk_id
            chunk_id = meta.chunk_id
            if chunk_id not in best_score_by_chunk or score > best_score_by_chunk[chunk_id]:
                best_score_by_chunk[chunk_id] = score
                best_candidate_by_chunk[chunk_id] = RetrievedChunk(
                    chunk_id=chunk_id,
                    document_id=meta.document_id,
                    document_name=meta.document_name,
                    content=meta.chunk_text,
                    score=round(score, 6),
                    rank=0,  # assigned below
                )

        if stale_db_count:
            logger.warning(
                "FAISSRetriever — %d embedding_id(s) resolved from FAISS mapping "
                "but missing from DB. Reconciliation recommended. user_id=%d",
                stale_db_count, user_id,
            )

        # ── Step 12: Deterministic ordering ────────────────────────────────────
        # Primary: score descending (higher inner-product = more similar)
        # Secondary: chunk_id ascending (stable tie-break)
        unique_results = sorted(
            best_candidate_by_chunk.values(),
            key=lambda c: (-c.score, c.chunk_id),
        )

        # ── Step 13: Truncate to top_k and assign ranks ────────────────────────
        final_results = unique_results[:top_k]
        for rank, chunk in enumerate(final_results, start=1):
            chunk.rank = rank

        logger.info(
            "FAISSRetriever — search complete: "
            "user_id=%d top_k=%d raw_candidates=%d authorized=%d "
            "filtered=%d returned=%d",
            user_id, top_k, len(raw_candidates),
            authorized_count, filtered_count, len(final_results),
        )

        return final_results

    # ── Private helpers ────────────────────────────────────────────────────────

    def _resolve_parsed_document_ids(
        self,
        db: Session,
        document_id: str,
    ) -> set[str] | None:
        """
        Resolve a document_id to its set of parsed_document_ids.

        Returns None if the document does not exist.
        The caller is responsible for ownership validation (done via the
        metadata join — chunks carry user_id).

        Args:
            db          : Active SQLAlchemy session.
            document_id : Document UUID string.

        Returns:
            Set of parsed_document_id strings, or None if document not found.
        """
        from app.models.parsed_document import ParsedDocument

        rows = (
            db.query(ParsedDocument.id)
            .filter(ParsedDocument.document_id == document_id)
            .all()
        )
        if not rows:
            return None
        return {row[0] for row in rows}
