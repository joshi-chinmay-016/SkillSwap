"""
Retriever — Abstract base class for retrieval implementations (Day 71).

All retriever implementations must satisfy this interface.
The application depends only on Retriever, never on FAISSRetriever directly.

Current implementation:
    FAISSRetriever — backed by FAISSVectorStore (Day 70).
"""
from __future__ import annotations

import abc

from sqlalchemy.orm import Session

from app.retrieval.retrieval_models import RetrievedChunk


class Retriever(abc.ABC):
    """
    Abstract interface for a retrieval backend.

    Implementations are responsible for:
        - Searching the underlying vector store.
        - Resolving vector IDs to database records.
        - Applying ownership and lifecycle filters.
        - Deduplicating results.
        - Ordering results deterministically.

    Implementations must NOT:
        - Perform query embedding (that is the service's responsibility).
        - Commit database transactions.
        - Expose raw FAISS IDs, embedding vectors, or filesystem paths.
        - Return unauthorized chunks.
    """

    @abc.abstractmethod
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
        Search for the most relevant chunks matching the query vector.

        Args:
            db                   : Active read-only SQLAlchemy session.
            query_vector         : Pre-computed query embedding from the provider.
            top_k                : Maximum number of results to return.
            user_id              : Authenticated user ID for ownership enforcement.
            similarity_threshold : Minimum score. Candidates below this are excluded.
            document_id          : Optional document UUID to restrict retrieval scope.

        Returns:
            List of RetrievedChunk, ordered best-first, at most top_k items.
            May return fewer than top_k if not enough authorized results exist.

        Raises:
            VectorStoreSearchError     : Vector search failed.
            MetadataResolutionError    : PostgreSQL lookup failed.
            RetrievalUnavailableError  : Vector store not ready.
        """
        ...
