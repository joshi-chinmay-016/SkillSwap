"""
Day 75 Part A2 — Context Optimization Test Suite.

Tests DefaultContextOptimizer across deterministic optimization rules:
    - Exact duplicate chunk removal (chunk_id and content hash)
    - Redundancy / high textual overlap reduction
    - Unique evidence preservation across distinct documents
    - Token budget enforcement
    - Relative retrieval rank order preservation
    - Configurable pass-through / safe rollback flag
    - Non-mutation of original input list and chunk objects

All tests use mock data — no database, FAISS, or external LLM calls.
"""
from __future__ import annotations

import pytest

from app.rag.optimization import (
    ContextOptimizer,
    DefaultContextOptimizer,
    OptimizationReason,
)
from app.retrieval.retrieval_models import RetrievedChunk


def make_chunk(
    chunk_id: str = "c1",
    document_id: str = "d1",
    document_name: str = "Test Doc",
    content: str = "FastAPI uses dependency injection.",
    score: float = 0.90,
    rank: int = 1,
) -> RetrievedChunk:
    return RetrievedChunk(
        chunk_id=chunk_id,
        document_id=document_id,
        document_name=document_name,
        content=content,
        score=score,
        rank=rank,
    )


# ═══════════════════════════════════════════════════════════════════════════════
# Context Optimization Tests
# ═══════════════════════════════════════════════════════════════════════════════


class TestDefaultContextOptimizer:
    def test_empty_chunks_returns_empty_result(self):
        optimizer = DefaultContextOptimizer(max_tokens=2048)
        res = optimizer.optimize([])
        assert res.original_chunk_count == 0
        assert res.optimized_chunk_count == 0
        assert res.optimized_chunks == []

    def test_exact_duplicate_chunk_id_removed(self):
        c1 = make_chunk(chunk_id="c1", rank=1)
        c2 = make_chunk(chunk_id="c1", rank=2)  # Duplicate chunk_id

        optimizer = DefaultContextOptimizer()
        res = optimizer.optimize([c1, c2])

        assert res.original_chunk_count == 2
        assert res.optimized_chunk_count == 1
        assert res.removed_duplicate_count == 1
        assert res.optimized_chunks[0].rank == 1

    def test_exact_duplicate_content_removed(self):
        c1 = make_chunk(chunk_id="c1", content="Exact identical content string.", rank=1)
        c2 = make_chunk(chunk_id="c2", content="Exact identical content string.", rank=2)

        optimizer = DefaultContextOptimizer()
        res = optimizer.optimize([c1, c2])

        assert res.original_chunk_count == 2
        assert res.optimized_chunk_count == 1
        assert res.removed_duplicate_count == 1
        assert res.records[1].reason == OptimizationReason.EXACT_DUPLICATE

    def test_high_textual_overlap_reduced(self):
        c1 = make_chunk(
            chunk_id="c1", document_id="d1", rank=1,
            content="FastAPI is a modern fast web framework for building APIs with Python."
        )
        c2 = make_chunk(
            chunk_id="c2", document_id="d1", rank=2,
            content="FastAPI is a modern fast web framework for building APIs with Python language."
        )

        optimizer = DefaultContextOptimizer(overlap_threshold=0.80)
        res = optimizer.optimize([c1, c2])

        assert res.original_chunk_count == 2
        assert res.optimized_chunk_count == 1
        assert res.removed_overlap_count == 1
        assert res.records[1].reason == OptimizationReason.HIGH_TEXTUAL_OVERLAP

    def test_unique_evidence_preserved_across_documents(self):
        c1 = make_chunk(
            chunk_id="c1", document_id="d1", rank=1,
            content="FastAPI uses dependency injection."
        )
        c2 = make_chunk(
            chunk_id="c2", document_id="d2", rank=2,
            content="PostgreSQL stores JSON documents and relational data."
        )

        optimizer = DefaultContextOptimizer(overlap_threshold=0.85)
        res = optimizer.optimize([c1, c2])

        assert res.original_chunk_count == 2
        assert res.optimized_chunk_count == 2
        assert res.removed_overlap_count == 0

    def test_stable_rank_ordering_preserved(self):
        """Relative rank order of kept chunks must match original retrieval order."""
        c1 = make_chunk(chunk_id="c1", rank=1, content="Topic A DI")
        c2 = make_chunk(chunk_id="c1", rank=2, content="Topic A DI")  # Dup, dropped
        c3 = make_chunk(chunk_id="c3", rank=3, content="Topic B REST")

        optimizer = DefaultContextOptimizer()
        res = optimizer.optimize([c1, c2, c3])

        assert [c.chunk_id for c in res.optimized_chunks] == ["c1", "c3"]
        assert res.optimized_chunks[0].rank == 1
        assert res.optimized_chunks[1].rank == 3

    def test_token_budget_enforced(self):
        # 10 tokens limit = ~40 chars
        optimizer = DefaultContextOptimizer(max_tokens=10)

        c1 = make_chunk(chunk_id="c1", content="Short text.", rank=1)  # ~11 chars = 2 tokens
        c2 = make_chunk(chunk_id="c2", content="X" * 200, rank=2)      # ~200 chars = 50 tokens

        res = optimizer.optimize([c1, c2])
        assert res.optimized_chunk_count == 1
        assert res.removed_budget_count == 1
        assert res.records[1].reason == OptimizationReason.CONTEXT_BUDGET

    def test_disabled_pass_through(self):
        c1 = make_chunk(chunk_id="c1", rank=1)
        c2 = make_chunk(chunk_id="c1", rank=2)

        optimizer = DefaultContextOptimizer(enabled=False)
        res = optimizer.optimize([c1, c2])

        assert res.original_chunk_count == 2
        assert res.optimized_chunk_count == 2
        assert len(res.optimized_chunks) == 2

    def test_input_list_not_mutated(self):
        c1 = make_chunk(chunk_id="c1", rank=1)
        c2 = make_chunk(chunk_id="c1", rank=2)
        orig_list = [c1, c2]

        optimizer = DefaultContextOptimizer()
        res = optimizer.optimize(orig_list)

        assert len(orig_list) == 2
        assert orig_list[0] == c1
        assert orig_list[1] == c2
