"""
Day 72 Part A1 — Retrieval → Context Integration Test Suite.

Tests the integration between the Day 71 Retriever layer and the Day 72 A1
ContextBuilder layer.  Uses mocked FAISS to avoid real vector store dependency.

Verifies:
    - Retrieval results are passed correctly to ContextBuilder
    - Relevance ordering (rank) is preserved through the pipeline
    - Duplicates from retrieval are removed by ContextBuilder
    - Source metadata (document_name, chunk_id, score) is retained
    - Context limits (max_chunks, max_characters) are respected
    - Empty retrieval produces a valid empty ContextResult
    - Unauthorized content never enters the context (retrieval layer responsibility)
    - No LLM is called

No real FAISS, no real DB, no real LLM.
"""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from app.rag.context_builder import DefaultContextBuilder
from app.rag.context_models import ContextRequest, ContextResult
from app.retrieval.retrieval_models import RetrievalResponse, RetrievedChunk


# ── Helpers ───────────────────────────────────────────────────────────────────


def make_chunk(
    chunk_id: str = "c1",
    document_id: str = "d1",
    document_name: str = "Test Document",
    content: str = "Sample content about the topic.",
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


def make_mock_retrieval_service(
    chunks: list[RetrievedChunk],
) -> MagicMock:
    """Mock RetrievalService that returns the given chunks."""
    mock = MagicMock()
    response = RetrievalResponse(
        results=chunks,
        total=len(chunks),
        query_duration_ms=10.0,
        embedding_ms=5.0,
        faiss_ms=3.0,
        db_ms=2.0,
    )
    mock.retrieve.return_value = response
    return mock


def pipeline(
    chunks: list[RetrievedChunk],
    max_chunks: int = 10,
    max_characters: int = 12000,
    max_tokens: int = 3000,
) -> ContextResult:
    """
    Run the Retriever → ContextBuilder pipeline with mocked retrieval.

    Args:
        chunks        : The authorized retrieved chunks to simulate.
        max_chunks    : Context builder chunk limit.
        max_characters: Context builder character limit.
        max_tokens    : Context builder token budget.

    Returns:
        ContextResult from DefaultContextBuilder.
    """
    mock_retrieval = make_mock_retrieval_service(chunks)
    builder = DefaultContextBuilder(
        max_chunks=max_chunks,
        max_characters=max_characters,
        max_tokens=max_tokens,
    )

    # Simulate the pipeline:
    # 1. Call retrieval service (mocked)
    db = MagicMock()
    retrieval_response = mock_retrieval.retrieve(db, request=MagicMock(), user_id=1)

    # 2. Pass results to ContextBuilder
    context_result = builder.build(
        ContextRequest(retrieved_chunks=retrieval_response.results)
    )
    return context_result


# ── Empty retrieval ───────────────────────────────────────────────────────────


class TestEmptyRetrieval:
    def test_empty_retrieval_produces_empty_context(self):
        result = pipeline([])

        assert isinstance(result, ContextResult)
        assert result.context_text == ""
        assert result.chunk_count == 0
        assert result.sources == []
        assert result.truncated is False

    def test_empty_retrieval_does_not_crash(self):
        result = pipeline([])
        assert result is not None


# ── Ordering preservation ─────────────────────────────────────────────────────


class TestOrderingPreservation:
    def test_rank_order_preserved_in_context(self):
        """Chunk rank order from Retriever must be preserved in ContextResult.sources."""
        chunks = [
            make_chunk(chunk_id="c3", rank=3, score=0.70, content="Third item"),
            make_chunk(chunk_id="c1", rank=1, score=0.95, content="First item"),
            make_chunk(chunk_id="c2", rank=2, score=0.85, content="Second item"),
        ]
        result = pipeline(chunks)

        source_ranks = [s.rank for s in result.sources]
        assert source_ranks == sorted(source_ranks), \
            f"Expected ascending rank order, got {source_ranks}"

    def test_best_ranked_appears_first_in_context_text(self):
        chunks = [
            make_chunk(chunk_id="c2", rank=2, content="SECOND"),
            make_chunk(chunk_id="c1", rank=1, content="FIRST"),
        ]
        result = pipeline(chunks)

        pos_first = result.context_text.index("FIRST")
        pos_second = result.context_text.index("SECOND")
        assert pos_first < pos_second

    def test_score_preserved_in_sources(self):
        chunks = [
            make_chunk(chunk_id="c1", rank=1, score=0.9123),
            make_chunk(chunk_id="c2", rank=2, score=0.7654),
        ]
        result = pipeline(chunks)

        scores_by_id = {s.chunk_id: s.score for s in result.sources}
        assert abs(scores_by_id["c1"] - 0.9123) < 1e-4
        assert abs(scores_by_id["c2"] - 0.7654) < 1e-4


# ── Deduplication ─────────────────────────────────────────────────────────────


class TestDeduplication:
    def test_duplicate_chunk_id_from_retrieval_deduplicated(self):
        """
        Defensive deduplication: if Retriever returns the same chunk_id twice
        (e.g., from re-indexing), ContextBuilder keeps only the best-ranked one.
        """
        chunks = [
            make_chunk(chunk_id="dup", rank=1, score=0.95, content="Best occurrence"),
            make_chunk(chunk_id="dup", rank=2, score=0.80, content="Duplicate occurrence"),
        ]
        result = pipeline(chunks)

        assert result.chunk_count == 1
        assert result.sources[0].chunk_id == "dup"
        assert result.sources[0].rank == 1
        assert "Best occurrence" in result.context_text
        assert "Duplicate occurrence" not in result.context_text

    def test_no_deduplication_for_different_chunk_ids(self):
        """Different chunk IDs from the same document should not be merged."""
        chunks = [
            make_chunk(chunk_id="c1", rank=1, document_id="d1", content="Part 1"),
            make_chunk(chunk_id="c2", rank=2, document_id="d1", content="Part 2"),
        ]
        result = pipeline(chunks)

        assert result.chunk_count == 2


# ── Source metadata retention ─────────────────────────────────────────────────


class TestSourceMetadata:
    def test_document_name_retained(self):
        chunk = make_chunk(document_name="FastAPI Deep Dive", chunk_id="c1")
        result = pipeline([chunk])

        assert result.sources[0].document_name == "FastAPI Deep Dive"

    def test_chunk_id_retained(self):
        chunk = make_chunk(chunk_id="specific-chunk-uuid")
        result = pipeline([chunk])

        assert result.sources[0].chunk_id == "specific-chunk-uuid"

    def test_document_id_retained(self):
        chunk = make_chunk(document_id="doc-uuid-123")
        result = pipeline([chunk])

        assert result.sources[0].document_id == "doc-uuid-123"

    def test_rank_and_score_retained(self):
        chunk = make_chunk(rank=3, score=0.777)
        result = pipeline([chunk])

        assert result.sources[0].rank == 3
        assert abs(result.sources[0].score - 0.777) < 1e-4

    def test_multiple_source_metadata_all_present(self):
        chunks = [
            make_chunk(chunk_id="c1", document_name="Doc A", rank=1),
            make_chunk(chunk_id="c2", document_name="Doc B", rank=2),
        ]
        result = pipeline(chunks)

        names = {s.document_name for s in result.sources}
        assert "Doc A" in names
        assert "Doc B" in names


# ── Context limits ────────────────────────────────────────────────────────────


class TestContextLimits:
    def test_max_chunks_respected(self):
        chunks = [make_chunk(chunk_id=f"c{i}", rank=i) for i in range(1, 7)]
        result = pipeline(chunks, max_chunks=3)

        assert result.chunk_count == 3
        assert result.truncated is True

    def test_max_characters_respected(self):
        """
        Each chunk has ~200 chars of content; character limit of 300 should
        allow roughly one chunk (given XML overhead).
        """
        chunks = [
            make_chunk(chunk_id=f"c{i}", rank=i, content="C" * 200)
            for i in range(1, 5)
        ]
        result = pipeline(chunks, max_chunks=10, max_characters=300)

        assert result.truncated is True
        # At most the budget's worth of content
        assert result.character_count <= 300 + 500  # tags have overhead

    def test_single_chunk_within_budget_not_truncated(self):
        chunk = make_chunk(content="Short content")
        result = pipeline([chunk])

        assert result.chunk_count == 1
        assert result.truncated is False

    def test_context_text_is_bounded(self):
        chunks = [make_chunk(chunk_id=f"c{i}", rank=i, content="X" * 1000) for i in range(1, 4)]
        result = pipeline(chunks, max_characters=2000)

        assert len(result.context_text) <= 2000 + 1000  # overhead for XML


# ── Context formatting ────────────────────────────────────────────────────────


class TestContextFormatting:
    def test_context_has_xml_boundary(self):
        chunk = make_chunk()
        result = pipeline([chunk])

        assert result.context_text.startswith("<retrieved_context>")
        assert result.context_text.endswith("</retrieved_context>")

    def test_content_present_in_context_text(self):
        chunk = make_chunk(content="Dependency injection is a design pattern.")
        result = pipeline([chunk])

        assert "Dependency injection is a design pattern." in result.context_text

    def test_document_boundaries_preserved_for_multiple_docs(self):
        chunks = [
            make_chunk(chunk_id="c1", document_id="d1", document_name="Doc A", rank=1, content="A content"),
            make_chunk(chunk_id="c2", document_id="d2", document_name="Doc B", rank=2, content="B content"),
        ]
        result = pipeline(chunks)

        # Each chunk has its own <source> block
        assert result.context_text.count("<source") == 2
        assert result.context_text.count("</source>") == 2
        assert "A content" in result.context_text
        assert "B content" in result.context_text


# ── Authorization boundary ────────────────────────────────────────────────────


class TestAuthorizationBoundary:
    def test_context_builder_only_sees_retriever_output(self):
        """
        Authorization is the Retriever's responsibility (Day 71).
        ContextBuilder only processes what the Retriever returns.
        This test verifies that the pipeline boundary is correct:
        ContextBuilder does not add any chunks that were not in the
        Retriever's response.
        """
        authorized_chunk = make_chunk(
            chunk_id="authorized", content="Authorized content"
        )
        result = pipeline([authorized_chunk])

        assert result.chunk_count == 1
        assert result.sources[0].chunk_id == "authorized"

    def test_only_retriever_provided_chunks_in_context(self):
        """If Retriever returns 2 authorized chunks, context has exactly 2."""
        chunks = [
            make_chunk(chunk_id="auth1", rank=1),
            make_chunk(chunk_id="auth2", rank=2),
        ]
        result = pipeline(chunks)

        context_chunk_ids = {s.chunk_id for s in result.sources}
        assert context_chunk_ids == {"auth1", "auth2"}
        # No extra chunks injected
        assert result.chunk_count == 2


# ── No LLM ───────────────────────────────────────────────────────────────────


class TestNoLLMCalled:
    def test_pipeline_does_not_call_any_llm(self):
        """Integration test must not call any LLM — this is Part A1 only."""
        # We use a real DefaultContextBuilder; if it called an LLM it would raise
        # (since no Gemini API key is configured in test env)
        chunks = [make_chunk()]
        # If this succeeds without error, no LLM was called
        result = pipeline(chunks)
        assert result is not None
        assert result.chunk_count == 1
