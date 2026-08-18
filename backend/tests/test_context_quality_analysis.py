"""
Day 75 Part A1 — Context Quality Analysis Test Suite.

Tests ContextSnapshot, ContextAnalyzer, and quality metrics across all 9 quality dimensions:
Relevance, Redundancy, Overlap, Diversity, Concentration, Ordering, Size/Tokens,
Budget/Truncation, Evidence Sufficiency.

All tests use mock data — no database, FAISS, or external LLM calls.
"""
from __future__ import annotations

import pytest

from app.rag.analysis import (
    AggregateQualityReport,
    ContextAnalyzer,
    ContextQualityAnalysis,
    ContextSnapshot,
    QualityCategory,
)
from app.retrieval.retrieval_models import RetrievedChunk


def make_chunk(
    chunk_id: str = "c1",
    document_id: str = "d1",
    document_name: str = "Test Doc",
    content: str = "FastAPI is a modern web framework for Python.",
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
# ContextSnapshot Tests
# ═══════════════════════════════════════════════════════════════════════════════


class TestContextSnapshot:
    def test_snapshot_from_empty_chunks(self):
        snapshot = ContextSnapshot.from_chunks([], query="empty query")
        assert snapshot.retrieved_chunk_count == 0
        assert snapshot.unique_document_count == 0
        assert snapshot.total_character_count == 0
        assert snapshot.estimated_token_count == 0

    def test_snapshot_from_valid_chunks(self):
        c1 = make_chunk(chunk_id="c1", document_id="d1", content="Hello world")
        c2 = make_chunk(chunk_id="c2", document_id="d2", content="Python programming")
        snapshot = ContextSnapshot.from_chunks([c1, c2], query="test query")

        assert snapshot.retrieved_chunk_count == 2
        assert snapshot.unique_document_count == 2
        assert snapshot.total_character_count == len("Hello world") + len("Python programming")
        assert snapshot.estimated_token_count == (len("Hello world") + len("Python programming")) // 4


# ═══════════════════════════════════════════════════════════════════════════════
# ContextAnalyzer Dimensions & Quality Categorization
# ═══════════════════════════════════════════════════════════════════════════════


class TestContextAnalyzer:
    def setup_method(self):
        self.analyzer = ContextAnalyzer(target_token_budget=100)

    def test_analyze_empty_chunks_returns_insufficient_category(self):
        analysis = self.analyzer.analyze_chunks([], query="Any query")
        assert QualityCategory.INSUFFICIENT_CONTEXT in analysis.categories
        assert analysis.chunk_count == 0

    def test_analyze_single_chunk_good_context(self):
        chunk = make_chunk()
        analysis = self.analyzer.analyze_chunks([chunk], query="What is FastAPI?")
        assert QualityCategory.GOOD_CONTEXT in analysis.categories
        assert analysis.diversity.unique_document_count == 1

    def test_exact_duplicate_chunks_flagged_redundant(self):
        c1 = make_chunk(chunk_id="dup-1", content="Identical content text for testing duplicate detection.")
        c2 = make_chunk(chunk_id="dup-1", content="Identical content text for testing duplicate detection.", rank=2)
        analysis = self.analyzer.analyze_chunks([c1, c2], query="test")

        assert QualityCategory.REDUNDANT_CONTEXT in analysis.categories
        assert analysis.redundancy.duplicate_chunk_count == 1
        assert analysis.redundancy.duplicate_ratio == 0.5

    def test_high_textual_overlap_flagged_redundant(self):
        c1 = make_chunk(
            chunk_id="c1", document_id="d1",
            content="FastAPI relies heavily on Python type hints and Pydantic for validation."
        )
        c2 = make_chunk(
            chunk_id="c2", document_id="d1", rank=2,
            content="FastAPI relies heavily on Python type hints and Pydantic validation framework."
        )
        analysis = self.analyzer.analyze_chunks([c1, c2], query="FastAPI validation")
        assert QualityCategory.REDUNDANT_CONTEXT in analysis.categories
        assert analysis.redundancy.textual_overlap_avg > 0.4

    def test_concentrated_document_flagged(self):
        # 5 chunks total, 4 from doc-1 (80% concentration)
        chunks = [
            make_chunk(chunk_id=f"c{i}", document_id="doc-1", content=f"Distinct content chunk {i}", rank=i)
            for i in range(1, 5)
        ]
        chunks.append(make_chunk(chunk_id="c5", document_id="doc-2", content="Distinct content chunk 5", rank=5))

        analysis = self.analyzer.analyze_chunks(chunks, query="test")
        assert QualityCategory.CONCENTRATED_CONTEXT in analysis.categories
        assert analysis.diversity.dominant_document_ratio == 0.8

    def test_oversized_context_flagged(self):
        # Set tiny budget (10 tokens = ~40 chars)
        tiny_analyzer = ContextAnalyzer(target_token_budget=10)
        c1 = make_chunk(content="A" * 500)
        analysis = tiny_analyzer.analyze_chunks([c1], query="test")
        assert QualityCategory.OVERSIZED_CONTEXT in analysis.categories
        assert analysis.budget.truncated is True

    def test_evidence_sufficiency_calculation(self):
        c1 = make_chunk(content="FastAPI uses dependency injection.")
        analysis = self.analyzer.analyze_chunks(
            [c1],
            query="What is FastAPI?",
            expected_facts=["dependency injection"],
            should_answer=True,
        )
        assert analysis.evidence.evidence_sufficient is True
        assert analysis.evidence.fact_coverage == 1.0


# ═══════════════════════════════════════════════════════════════════════════════
# Aggregate Report Tests
# ═══════════════════════════════════════════════════════════════════════════════


class TestAggregateReport:
    def setup_method(self):
        self.analyzer = ContextAnalyzer()

    def test_aggregate_empty_returns_zero(self):
        report = self.analyzer.compute_aggregate([])
        assert report.total_cases == 0

    def test_aggregate_multiple_analyses(self):
        a1 = self.analyzer.analyze_chunks([make_chunk(chunk_id="c1")])
        a2 = self.analyzer.analyze_chunks([make_chunk(chunk_id="c2")])

        report = self.analyzer.compute_aggregate([a1, a2])
        assert report.total_cases == 2
        assert report.good_context_count == 2
        assert report.avg_chunks_per_case == 1.0
        assert report.to_dict()["total_cases"] == 2
        assert isinstance(report.format_human_readable(), str)
