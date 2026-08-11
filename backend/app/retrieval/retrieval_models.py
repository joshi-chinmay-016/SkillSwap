"""
Retrieval models — typed request/response dataclasses (Day 71).

These are pure data containers with no database or FAISS dependencies.

RetrievalRequest : Validated input from the caller.
RetrievedChunk   : One result item returned to the caller.
RetrievalResponse: Final response wrapping all results + metadata.

Security:
    - No raw embedding vectors exposed.
    - No FAISS IDs exposed.
    - No filesystem paths exposed.
    - No database credentials exposed.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class RetrievalRequest:
    """
    A validated retrieval request.

    Fields:
        query                : Natural-language query string. Must be non-empty
                               and not whitespace-only. Max length enforced by service.
        top_k                : Maximum number of results to return.
                               1 <= top_k <= RETRIEVAL_MAX_TOP_K.
        similarity_threshold : Minimum inner-product score (0.0–1.0).
                               Candidates scoring below this are excluded.
                               0.0 = no threshold.
        document_id          : Optional UUID of a specific document to restrict
                               retrieval to. If None, search spans all of the
                               user's eligible knowledge.
    """

    query: str
    top_k: int = 5
    similarity_threshold: float = 0.0
    document_id: Optional[str] = None


@dataclass
class RetrievedChunk:
    """
    One result chunk returned by the retriever.

    Fields:
        chunk_id      : UUID of the Chunk record (PostgreSQL pk).
        document_id   : UUID of the parent Document.
        document_name : Human-readable document title.
        content       : Full text of the chunk (chunk_text).
        score         : Inner-product similarity score (higher = more relevant).
                        Range: –1.0 to +1.0; in practice 0.0–1.0 for
                        well-normalised Gemini embeddings.
        rank          : 1-based position in the final result list.
    """

    chunk_id: str
    document_id: str
    document_name: str
    content: str
    score: float
    rank: int


@dataclass
class RetrievalResponse:
    """
    Final response from the retrieval service.

    Fields:
        results           : Ordered list of RetrievedChunk, best-first.
        total             : Length of results (convenience field for the API layer).
        query_duration_ms : Total wall-clock time for the full retrieval pipeline.
        embedding_ms      : Time spent generating the query embedding.
        faiss_ms          : Time spent in FAISS search.
        db_ms             : Time spent in PostgreSQL metadata resolution.
    """

    results: list[RetrievedChunk] = field(default_factory=list)
    total: int = 0
    query_duration_ms: float = 0.0
    embedding_ms: float = 0.0
    faiss_ms: float = 0.0
    db_ms: float = 0.0
