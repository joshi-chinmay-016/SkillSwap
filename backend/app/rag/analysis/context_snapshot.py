"""
ContextSnapshot — Day 75 Part A1.

Captures a structured snapshot of retrieved context entering the ContextBuilder /
Grounding Engine.

Pure data container with no database, FAISS, or LLM dependencies.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from app.retrieval.retrieval_models import RetrievedChunk


@dataclass
class ContextSnapshot:
    """
    Structured representation of retrieved chunks entering the context pipeline.

    Fields:
        query                  : User query string.
        retrieved_chunk_count  : Number of authorized chunks returned by Retriever.
        selected_chunk_count   : Number of chunks selected for context.
        unique_document_count  : Number of unique document IDs in retrieved chunks.
        unique_source_count    : Number of unique document names in retrieved chunks.
        chunk_ids              : List of chunk_id UUID strings.
        document_ids           : List of parent document_id UUID strings.
        retrieval_scores       : Inner-product FAISS scores (higher = more relevant).
        chunk_lengths          : Character length of each retrieved chunk.
        total_character_count  : Sum of character lengths of all chunks.
        estimated_token_count  : Approximate token count (chars // 4).
        chunks                 : Reference to RetrievedChunk objects.
    """

    query: str = ""
    retrieved_chunk_count: int = 0
    selected_chunk_count: int = 0
    unique_document_count: int = 0
    unique_source_count: int = 0
    chunk_ids: list[str] = field(default_factory=list)
    document_ids: list[str] = field(default_factory=list)
    retrieval_scores: list[float] = field(default_factory=list)
    chunk_lengths: list[int] = field(default_factory=list)
    total_character_count: int = 0
    estimated_token_count: int = 0
    chunks: list[RetrievedChunk] = field(default_factory=list)

    @classmethod
    def from_chunks(
        cls,
        chunks: list[RetrievedChunk],
        query: str = "",
        selected_count: Optional[int] = None,
    ) -> "ContextSnapshot":
        """
        Construct a ContextSnapshot from a list of RetrievedChunk objects.

        Calculates metadata dimensions dynamically without modifying chunk objects.
        """
        chunk_ids = [c.chunk_id for c in chunks]
        doc_ids = [c.document_id for c in chunks]
        doc_names = {c.document_name for c in chunks if c.document_name}
        scores = [c.score for c in chunks]
        lengths = [len(c.content) for c in chunks if c.content]

        total_chars = sum(lengths)
        estimated_tokens = total_chars // 4

        return cls(
            query=query,
            retrieved_chunk_count=len(chunks),
            selected_chunk_count=selected_count if selected_count is not None else len(chunks),
            unique_document_count=len(set(doc_ids)),
            unique_source_count=len(doc_names) if doc_names else len(set(doc_ids)),
            chunk_ids=chunk_ids,
            document_ids=doc_ids,
            retrieval_scores=scores,
            chunk_lengths=lengths,
            total_character_count=total_chars,
            estimated_token_count=estimated_tokens,
            chunks=chunks,
        )
