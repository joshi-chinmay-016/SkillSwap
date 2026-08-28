"""
Vector Store Exceptions — Day 70.

Custom exception hierarchy for the FAISS Vector Storage layer.
Never expose raw FAISS internals outside this layer.

Exception tree:
    VectorStoreError (base)
    ├── VectorStoreInitializationError  — failed to initialise/load index
    ├── FAISSIndexError                 — FAISS operation failed unexpectedly
    ├── VectorDimensionMismatchError    — vector dim != index dim
    ├── VectorStorePersistenceError     — save/load failed
    ├── VectorMappingError              — ID mapping inconsistency
    ├── VectorIndexingError             — indexing pipeline failure
    ├── VectorRebuildError              — rebuild failed
    └── VectorConsistencyError          — PostgreSQL ↔ FAISS mismatch
"""
from __future__ import annotations


class VectorStoreError(Exception):
    """Base class for all vector-store-layer exceptions."""

    def __init__(self, message: str, *, cause: Exception | None = None) -> None:
        super().__init__(message)
        self.cause = cause
        self.message = message

    def __str__(self) -> str:
        if self.cause:
            return f"{self.message} (caused by: {self.cause})"
        return self.message

    @property
    def is_recoverable(self) -> bool:
        """Whether this error is safe to retry."""
        return False


class VectorStoreInitializationError(VectorStoreError):
    """
    Raised when the vector store cannot be initialised or loaded.

    Examples:
        - Index file is corrupted.
        - Dimension mismatch detected during load.
        - Storage directory is not writable.
    """

    @property
    def is_recoverable(self) -> bool:
        return False


class FAISSIndexError(VectorStoreError):
    """
    Raised when a FAISS operation fails unexpectedly.

    Examples:
        - faiss.add() raises an internal error.
        - faiss.remove_ids() fails.
        - Unexpected FAISS library exception.
    """

    @property
    def is_recoverable(self) -> bool:
        # FAISS internal errors may be transient (memory pressure, etc.)
        return True


class VectorDimensionMismatchError(VectorStoreError):
    """
    Raised when an embedding vector's dimension does not match the index dimension.

    Examples:
        - Embedding dim = 1536, FAISS index dim = 768.
        - Attempting to load an index file created with a different model.

    This is NOT recoverable — the configuration or data must be fixed first.
    """

    def __init__(
        self,
        message: str,
        *,
        expected_dimension: int | None = None,
        actual_dimension: int | None = None,
        embedding_id: str | None = None,
        cause: Exception | None = None,
    ) -> None:
        super().__init__(message, cause=cause)
        self.expected_dimension = expected_dimension
        self.actual_dimension = actual_dimension
        self.embedding_id = embedding_id

    @property
    def is_recoverable(self) -> bool:
        return False


class VectorStorePersistenceError(VectorStoreError):
    """
    Raised when the index cannot be saved to or loaded from disk.

    Examples:
        - Disk full.
        - Permission denied on index directory.
        - Atomic rename failed.
        - File read returns corrupt data.
    """

    @property
    def is_recoverable(self) -> bool:
        # IO errors may be transient (e.g., temporary disk full)
        return True


class VectorMappingError(VectorStoreError):
    """
    Raised when the FAISS ID ↔ embedding ID mapping is inconsistent.

    Examples:
        - Mapping file missing after index file exists.
        - Duplicate faiss_id assigned to different embedding_ids.
        - Mapping references an embedding_id not in the database.
    """

    @property
    def is_recoverable(self) -> bool:
        return False


class VectorIndexingError(VectorStoreError):
    """
    Raised when an embedding cannot be added to the vector index.

    Examples:
        - Vector fails pre-indexing validation.
        - FAISS add operation fails for this vector.

    Individual failures within a batch should use this exception.
    Callers should log and continue with the next vector.
    """

    def __init__(
        self,
        message: str,
        *,
        embedding_id: str | None = None,
        cause: Exception | None = None,
    ) -> None:
        super().__init__(message, cause=cause)
        self.embedding_id = embedding_id

    @property
    def is_recoverable(self) -> bool:
        return False


class VectorRebuildError(VectorStoreError):
    """
    Raised when a full index rebuild fails.

    The caller must ensure the old index is preserved when this is raised.
    The new index must NOT be promoted if rebuild fails.
    """

    @property
    def is_recoverable(self) -> bool:
        return False


class VectorConsistencyError(VectorStoreError):
    """
    Raised when a PostgreSQL ↔ FAISS consistency check detects divergence.

    Examples:
        - Embedding in DB but no corresponding FAISS vector.
        - FAISS vector has no mapping to a DB embedding.
        - vector_index_entries count != FAISS index size.

    This is informational — the system logs details and waits for reconciliation.
    """

    def __init__(
        self,
        message: str,
        *,
        missing_in_faiss: int = 0,
        orphaned_in_faiss: int = 0,
        cause: Exception | None = None,
    ) -> None:
        super().__init__(message, cause=cause)
        self.missing_in_faiss = missing_in_faiss
        self.orphaned_in_faiss = orphaned_in_faiss

    @property
    def is_recoverable(self) -> bool:
        return False
