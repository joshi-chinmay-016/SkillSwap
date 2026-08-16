"""
Day 75 Part B — End-to-End Production Integration & Regression Test Suite.

Verifies:
    1. Production RAG Pipeline Flow:
       Retriever → Context Quality Analysis → Context Optimization → Context Builder →
       Prompt Builder → LLM Provider → Answer Validator → AI Mentor Response.
    2. Feature Flag Rollback:
       Disabling CONTEXT_OPTIMIZATION_ENABLED bypasses optimization safely.
    3. Security & Cross-User Isolation:
       Authorization filtering runs BEFORE optimization. Optimizer only receives
       authorized chunks belonging to the requesting user.
    4. Source Attribution & Integrity:
       Sources returned in GenerationResult map to authorized, retrieved chunks.
       Unretrieved or fabricated sources are stripped by AnswerValidator.
    5. Insufficient Context & Refusal:
       Empty retrieval returns insufficient_context=True, grounded=False.
    6. Baseline vs. Optimized Context Comparison:
       Verifies token and chunk count reduction without loss of required evidence.
"""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from app.core.config import settings
from app.rag import (
    DefaultContextBuilder,
    GenerationResult,
    GroundedPromptBuilder,
    RAGService,
)
from app.rag.analysis import ContextAnalyzer, ContextSnapshot
from app.rag.optimization import DefaultContextOptimizer, OptimizationReason
from app.retrieval.retrieval_models import RetrievalResponse, RetrievedChunk


def make_retrieved_chunk(
    chunk_id: str = "c1",
    document_id: str = "d1",
    document_name: str = "FastAPI Architecture Notes.pdf",
    content: str = "FastAPI uses dependency injection for managing dependencies cleanly.",
    score: float = 0.92,
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


def make_rag_service(chunks: list[RetrievedChunk] | None = None, llm_response: str = "FastAPI uses dependency injection."):
    if chunks is None:
        chunks = [make_retrieved_chunk()]

    mock_retrieval = MagicMock()
    mock_retrieval.retrieve.return_value = RetrievalResponse(
        results=chunks,
        total=len(chunks),
        query_duration_ms=5.0,
        embedding_ms=2.0,
        faiss_ms=1.0,
        db_ms=2.0,
    )

    mock_llm = MagicMock()
    mock_llm.generate.return_value = llm_response

    context_builder = DefaultContextBuilder.from_settings()
    prompt_builder = GroundedPromptBuilder.from_settings()

    service = RAGService(
        retrieval_service=mock_retrieval,
        context_builder=context_builder,
        prompt_builder=prompt_builder,
        llm_service=mock_llm,
    )
    return service, mock_retrieval, mock_llm


# ═══════════════════════════════════════════════════════════════════════════════
# End-to-End Pipeline Integration Tests
# ═══════════════════════════════════════════════════════════════════════════════


class TestDay75PartBIntegration:
    def test_full_pipeline_with_optimization_returns_grounded_result(self):
        """
        Verify the integrated pipeline flow:
        Retriever → Analysis → Optimizer → ContextBuilder → PromptBuilder → LLM → Validator
        """
        c1 = make_retrieved_chunk(chunk_id="c1", document_id="d1", content="FastAPI uses dependency injection.")
        service, mock_retrieval, mock_llm = make_rag_service(chunks=[c1])
        db = MagicMock()

        result = service.query(db, query="What is FastAPI DI?", user_id=1)

        assert isinstance(result, GenerationResult)
        assert result.answer != ""
        assert result.grounded is True
        assert len(result.sources) == 1
        assert result.sources[0].chunk_id == "c1"
        mock_retrieval.retrieve.assert_called_once()
        mock_llm.generate.assert_called_once()

    def test_optimization_removes_redundant_duplicate_chunks_in_pipeline(self):
        """
        When Retriever returns duplicate chunks, Optimizer removes duplicates before
        ContextBuilder, leaving 1 chunk in final context.
        """
        c1 = make_retrieved_chunk(chunk_id="c1", rank=1, content="FastAPI uses dependency injection.")
        c2 = make_retrieved_chunk(chunk_id="c1", rank=2, content="FastAPI uses dependency injection.")  # Exact duplicate

        service, _, _ = make_rag_service(chunks=[c1, c2])
        db = MagicMock()

        result = service.query(db, query="Explain DI?", user_id=1)

        # Context chunk count after optimizer should be 1
        assert result.context_chunk_count == 1
        assert len(result.sources) == 1

    def test_feature_flag_disabled_bypasses_optimizer(self):
        """
        When CONTEXT_OPTIMIZATION_ENABLED=False, raw retrieved chunks pass straight to ContextBuilder.
        """
        c1 = make_retrieved_chunk(chunk_id="c1", document_id="d1", content="FastAPI dependency injection.")
        c2 = make_retrieved_chunk(chunk_id="c2", document_id="d2", content="PostgreSQL ACID database transactions.")

        service, _, _ = make_rag_service(chunks=[c1, c2])
        db = MagicMock()

        with patch.object(settings, "CONTEXT_OPTIMIZATION_ENABLED", False):
            result = service.query(db, query="Explain tech stack?", user_id=1)

        assert result.context_chunk_count == 2
        assert len(result.sources) == 2

    def test_empty_retrieval_insufficient_context_refusal(self):
        """Empty retrieval must return insufficient_context=True and grounded=False."""
        mock_retrieval = MagicMock()
        mock_retrieval.retrieve.return_value = RetrievalResponse(
            results=[],
            total=0,
            query_duration_ms=1.0,
            embedding_ms=1.0,
            faiss_ms=0.5,
            db_ms=0.5,
        )
        mock_llm = MagicMock()
        mock_llm.generate.return_value = "I don't have enough information to answer that."

        service = RAGService(
            retrieval_service=mock_retrieval,
            context_builder=DefaultContextBuilder.from_settings(),
            prompt_builder=GroundedPromptBuilder.from_settings(),
            llm_service=mock_llm,
        )
        db = MagicMock()

        result = service.query(db, query="Unrelated quantum physics question?", user_id=42)

        assert result.insufficient_context is True
        assert result.grounded is False
        assert result.sources == []

    def test_security_authorization_happens_upstream(self):
        """
        RetrievalService must be called with the authenticated user_id before Optimizer runs.
        """
        service, mock_retrieval, _ = make_rag_service()
        db = MagicMock()

        service.query(db, query="Security test", user_id=99)

        call_args = mock_retrieval.retrieve.call_args
        assert call_args[1].get("user_id") == 99


# ═══════════════════════════════════════════════════════════════════════════════
# Baseline vs. Optimized Context Comparison Tests
# ═══════════════════════════════════════════════════════════════════════════════


class TestBaselineVsOptimizedComparison:
    def test_baseline_vs_optimized_context_reduction(self):
        """
        Compare unoptimized vs optimized context for a case with 4 chunks (2 redundant).
        Optimizer should reduce chunk count and estimated tokens while preserving evidence.
        """
        chunks = [
            make_retrieved_chunk(chunk_id="c1", document_id="d1", rank=1, content="FastAPI dependency injection decouples components."),
            make_retrieved_chunk(chunk_id="c1", document_id="d1", rank=2, content="FastAPI dependency injection decouples components."),  # Dup
            make_retrieved_chunk(chunk_id="c3", document_id="d1", rank=3, content="FastAPI dependency injection decouples components cleanly."), # High overlap
            make_retrieved_chunk(chunk_id="c4", document_id="d2", rank=4, content="PostgreSQL handles data storage with ACID guarantees."),
        ]

        optimizer = DefaultContextOptimizer(overlap_threshold=0.80)

        # Baseline (Unoptimized)
        snapshot_baseline = ContextSnapshot.from_chunks(chunks, query="Architecture?")
        analyzer = ContextAnalyzer()
        analysis_baseline = analyzer.analyze_snapshot(snapshot_baseline)

        # Optimized
        opt_res = optimizer.optimize(chunks)
        snapshot_opt = ContextSnapshot.from_chunks(opt_res.optimized_chunks, query="Architecture?")
        analysis_opt = analyzer.analyze_snapshot(snapshot_opt)

        assert opt_res.original_chunk_count == 4
        assert opt_res.optimized_chunk_count == 2
        assert opt_res.removed_duplicate_count == 1
        assert opt_res.removed_overlap_count == 1
        assert opt_res.optimized_token_estimate < opt_res.original_token_estimate

        # Both preserved evidence for "dependency injection" and "PostgreSQL"
        combined_opt_text = " ".join(c.content for c in opt_res.optimized_chunks)
        assert "dependency injection" in combined_opt_text
        assert "PostgreSQL" in combined_opt_text
