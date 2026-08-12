"""
RAG Context Models — typed request/response dataclasses (Day 72 A1).

These are pure data containers; no database, FAISS, or LLM dependencies.

ContextRequest : Inputs consumed by ContextBuilder.
ContextSource  : Source traceability record for one selected chunk.
ContextResult  : Output produced by ContextBuilder, ready for PromptBuilder.

Security:
    - No raw embedding vectors exposed.
    - No FAISS IDs exposed.
    - No filesystem paths exposed.
    - No database credentials or internal state exposed.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from app.retrieval.retrieval_models import RetrievedChunk


@dataclass
class ContextRequest:
    """
    Input to ContextBuilder.

    Fields:
        retrieved_chunks  : Ordered list of authorized RetrievedChunks from
                            the Retriever (best-first, already deduplicated by
                            FAISSRetriever).  ContextBuilder applies a second,
                            defensive deduplication pass.
        max_chunks        : Override maximum chunk count for this request.
                            None → use settings.RAG_MAX_CONTEXT_CHUNKS.
        max_characters    : Override maximum character count.
                            None → use settings.RAG_MAX_CONTEXT_CHARACTERS.
        max_tokens        : Override approximate token budget.
                            None → use settings.RAG_MAX_CONTEXT_TOKENS.
        include_metadata  : Whether to include source metadata headers in the
                            formatted context text (default True).
    """

    retrieved_chunks: list[RetrievedChunk] = field(default_factory=list)
    max_chunks: Optional[int] = None
    max_characters: Optional[int] = None
    max_tokens: Optional[int] = None
    include_metadata: bool = True


@dataclass
class ContextSource:
    """
    Traceability record for one chunk selected into the context window.

    Every ContextSource maps directly to a RetrievedChunk that was included.
    The ordering mirrors the context text ordering (rank ascending).

    Fields:
        chunk_id      : UUID of the Chunk record (PostgreSQL pk).
        document_id   : UUID of the parent Document.
        document_name : Human-readable document title.
        rank          : 1-based position from the Retriever result list.
        score         : Inner-product similarity score (higher = more relevant).
    """

    chunk_id: str
    document_id: str
    document_name: str
    rank: int
    score: float


@dataclass
class ContextResult:
    """
    Output from ContextBuilder — bounded, formatted context ready for PromptBuilder.

    Fields:
        context_text      : Formatted context string with explicit source boundaries.
                            Wrapped in <retrieved_context> tags for prompt-injection
                            safety.  Empty string if no chunks were selected.
        sources           : Ordered list of ContextSource records for every chunk
                            included in context_text.  Used for source attribution.
        chunk_count       : Number of chunks selected into the context window.
        character_count   : Total character length of context_text.
        token_estimate    : Approximate token count (characters // 4).
                            Documented as an estimate — NOT exact token accounting.
        truncated         : True if one or more chunks were dropped or truncated
                            due to budget limits.
    """

    context_text: str = ""
    sources: list[ContextSource] = field(default_factory=list)
    chunk_count: int = 0
    character_count: int = 0
    token_estimate: int = 0
    truncated: bool = False
