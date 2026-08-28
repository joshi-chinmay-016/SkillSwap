"""
VectorStore — Abstract base class for vector index backends (Day 70).

All vector store implementations must satisfy this interface.
The application depends only on VectorStore, never on FAISSVectorStore directly.

Design goals:
    - Provider-agnostic: swap FAISS for another backend without touching services.
    - Minimal API: only methods genuinely required by the current architecture.
    - Explicit lifecycle: initialization, mutation, persistence are clearly separated.
    - Health-observable: lightweight status without expensive index scans.

Current implementation:
    FAISSVectorStore — FAISS CPU exact-search index (IndexIDMap2 + IndexFlatIP)

Retrieval (Day 71):
    search() added in Day 71. IndexFlatIP returns inner-product scores;
    higher score = higher cosine similarity for L2-normalised vectors.
"""
from __future__ import annotations

import abc
from dataclasses import dataclass, field
from typing import Optional


# ── Health status dataclass ───────────────────────────────────────────────────

@dataclass
class VectorStoreHealth:
    """
    Lightweight status summary returned by health_check().

    Fields:
        is_initialized : True if the index has been loaded or created.
        is_loaded      : True if the index is currently in memory.
        dimension      : Configured/detected vector dimension, or 0 if unknown.
        vector_count   : Number of vectors currently indexed.
        persistence_ok : True if the index directory is writable.
        index_path     : Absolute path to the index file on disk.
        details        : Optional additional diagnostic string.
    """

    is_initialized: bool = False
    is_loaded: bool = False
    dimension: int = 0
    vector_count: int = 0
    persistence_ok: bool = False
    index_path: str = ""
    details: str = ""

    def as_dict(self) -> dict:
        """Return a log-safe dict representation."""
        return {
            "is_initialized": self.is_initialized,
            "is_loaded": self.is_loaded,
            "dimension": self.dimension,
            "vector_count": self.vector_count,
            "persistence_ok": self.persistence_ok,
            "index_path": self.index_path,
            "details": self.details,
        }


# ── Abstract interface ─────────────────────────────────────────────────────────

class VectorStore(abc.ABC):
    """
    Abstract interface for a vector index backend.

    Implementations must:
        - Be thread-safe for concurrent mutations.
        - Persist state atomically (no partial writes).
        - Map application embedding IDs to internal vector IDs.
        - Validate vector dimensions before every mutation.
        - Never log raw vector values or document text.

    Methods are synchronous to match the existing SQLAlchemy session pattern.
    """

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    @abc.abstractmethod
    def initialize_index(self) -> None:
        """
        Load an existing index from disk or create a new empty index.

        Must be called once before any other operation.
        If the index file exists: load and validate it.
        If the index file does not exist: create a new empty index.
        If the index file is corrupted: raise VectorStoreInitializationError.

        Raises:
            VectorStoreInitializationError : Index is corrupted or configuration invalid.
            VectorStorePersistenceError    : Disk read failed.
        """
        ...

    @abc.abstractmethod
    def save_index(self) -> None:
        """
        Atomically persist the current in-memory index to disk.

        Uses a temp file + rename strategy to avoid partial writes.
        If the write fails, the last known valid index must remain intact.

        Raises:
            VectorStorePersistenceError: Save failed.
        """
        ...

    @abc.abstractmethod
    def load_index(self) -> None:
        """
        Load the index from disk into memory.

        If the index does not exist on disk, raise VectorStoreInitializationError
        rather than silently creating an empty index (use initialize_index() for that).

        Raises:
            VectorStoreInitializationError : Index file not found or corrupted.
            VectorDimensionMismatchError   : Index dimension != configured dimension.
            VectorStorePersistenceError    : Disk read failed.
        """
        ...

    # ── Mutation ──────────────────────────────────────────────────────────────

    @abc.abstractmethod
    def add_vectors(
        self,
        vectors: list[list[float]],
        embedding_ids: list[str],
    ) -> dict[str, int | str]:
        """
        Add a batch of vectors to the index.

        Each vector is associated with a persistent embedding_id from PostgreSQL.
        The implementation assigns a stable internal vector ID (faiss_id) and
        maintains the bidirectional mapping.

        Args:
            vectors       : List of float vectors. All must have the correct dimension.
            embedding_ids : Matching list of embedding UUID strings from PostgreSQL.
                            Must have the same length as vectors.

        Returns:
            Dict mapping embedding_id → faiss_id for successfully added vectors.

        Raises:
            VectorDimensionMismatchError : A vector's dimension != index dimension.
            VectorIndexingError          : A vector failed validation or FAISS add.
            FAISSIndexError              : Unexpected FAISS library error.
        """
        ...

    @abc.abstractmethod
    def remove_vectors(self, embedding_ids: list[str]) -> int:
        """
        Remove vectors from the index by embedding_id.

        Vectors not found in the mapping are silently skipped.

        Args:
            embedding_ids: List of embedding UUID strings to remove.

        Returns:
            Number of vectors actually removed from the index.

        Raises:
            FAISSIndexError             : Unexpected FAISS library error.
            VectorStorePersistenceError : Save failed after removal.
        """
        ...

    @abc.abstractmethod
    def rebuild_index(
        self,
        vectors: list[list[float]],
        embedding_ids: list[str],
    ) -> None:
        """
        Safely rebuild the entire index from scratch.

        The strategy must ensure the old index is preserved if the rebuild fails.
        Only replaces the production index after the new index is fully built
        and validated.

        Args:
            vectors       : All vectors to include in the rebuilt index.
            embedding_ids : Matching list of embedding UUID strings.

        Raises:
            VectorRebuildError          : Rebuild failed; old index remains active.
            VectorDimensionMismatchError: A vector's dimension is wrong.
        """
        ...

    # ── Introspection ─────────────────────────────────────────────────────────

    @abc.abstractmethod
    def get_index_size(self) -> int:
        """
        Return the number of vectors currently in the index.

        Returns 0 if the index has not been initialised yet.
        """
        ...

    @abc.abstractmethod
    def get_dimension(self) -> int:
        """
        Return the configured vector dimension for this index.

        Raises:
            VectorStoreInitializationError: Dimension not yet determined.
        """
        ...

    @abc.abstractmethod
    def get_indexed_embedding_ids(self) -> set[str]:
        """
        Return the set of embedding_ids currently present in the index mapping.

        Used for idempotency checks and reconciliation.
        """
        ...

    @abc.abstractmethod
    def health_check(self) -> VectorStoreHealth:
        """
        Return a lightweight health status without performing expensive operations.

        Should not scan the entire index or perform disk reads.

        Returns:
            VectorStoreHealth dataclass.
        """
        ...

    # ── Retrieval ─────────────────────────────────────────────────────────────

    @abc.abstractmethod
    def search(
        self,
        query_vector: list[float],
        top_k: int,
    ) -> list[tuple[int, float]]:
        """
        Search the index for the top-k most similar vectors.

        The metric interpretation depends on the underlying index:
            IndexFlatIP  : Inner-product scores. Higher = more similar.
                           With L2-normalised vectors this equals cosine similarity.

        Args:
            query_vector : The query embedding. Must match the index dimension.
            top_k        : Number of candidates to return. Must be >= 1.

        Returns:
            List of (faiss_id, score) pairs, ordered by score descending.
            May be shorter than top_k if the index contains fewer vectors.
            Never contains FAISS sentinel ID -1.

        Raises:
            VectorStoreInitializationError : Index not initialized.
            VectorDimensionMismatchError   : Query vector dimension != index dimension.
            FAISSIndexError                : FAISS search failed unexpectedly.
        """
        ...
