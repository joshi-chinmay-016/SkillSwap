"""
Day 71 Retrieval — Exception hierarchy.

All retrieval-layer errors inherit from RetrievalError.
User-facing messages are concise; internal details belong in logs.

Exception tree:
    RetrievalError (base)
    ├── InvalidRetrievalRequestError  — bad query/top_k/threshold/document_id input
    ├── QueryEmbeddingError           — embedding provider failed on query
    ├── VectorStoreSearchError        — FAISS search failed
    ├── MetadataResolutionError       — PostgreSQL batch lookup failed
    └── RetrievalUnavailableError     — index not initialized / unavailable
"""
from __future__ import annotations


class RetrievalError(Exception):
    """Base class for all retrieval-layer exceptions."""

    def __init__(self, message: str, *, cause: Exception | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.cause = cause

    def __str__(self) -> str:
        if self.cause:
            return f"{self.message} (caused by: {type(self.cause).__name__}: {self.cause})"
        return self.message

    @property
    def is_recoverable(self) -> bool:
        """Whether callers may retry this operation."""
        return False


class InvalidRetrievalRequestError(RetrievalError):
    """
    Raised for invalid retrieval input before any external call is made.

    Examples:
        - Empty or whitespace-only query.
        - top_k < 1 or top_k > max_top_k.
        - similarity_threshold outside [0.0, 1.0].
        - document_id is not a valid UUID.
    """

    @property
    def is_recoverable(self) -> bool:
        return False  # Client must fix the request


class QueryEmbeddingError(RetrievalError):
    """
    Raised when the embedding provider fails to embed the user query.

    Examples:
        - Provider API returns 429 (rate limit).
        - Provider API returns 503.
        - Network timeout during query embedding.
    """

    @property
    def is_recoverable(self) -> bool:
        return True  # May succeed on retry


class VectorStoreSearchError(RetrievalError):
    """
    Raised when the FAISS vector search fails.

    Examples:
        - FAISS internal error during search.
        - Dimension mismatch between query vector and index.
    """

    @property
    def is_recoverable(self) -> bool:
        return False  # Likely configuration issue


class MetadataResolutionError(RetrievalError):
    """
    Raised when the PostgreSQL batch metadata lookup fails.

    Examples:
        - Database connection error during chunk/document fetch.
        - Unexpected ORM error.
    """

    @property
    def is_recoverable(self) -> bool:
        return True  # DB errors may be transient


class RetrievalUnavailableError(RetrievalError):
    """
    Raised when the retrieval infrastructure is unavailable.

    Examples:
        - FAISS index not initialized.
        - FAISS index file missing at startup.
        - VectorStore not yet loaded.

    This is distinct from "no results" — it signals an infrastructure fault.
    """

    @property
    def is_recoverable(self) -> bool:
        return False  # Requires operator intervention
