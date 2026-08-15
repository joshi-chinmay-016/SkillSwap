"""
ContextAnalyzer — Day 75 Part A1.

Performs diagnostic analysis over context entering the Grounded Answer Engine.

This class is DIAGNOSTIC ONLY.  It does NOT modify retrieved chunks, change
FAISS search parameters, rerank candidate vectors, or alter prompt construction.

Analysis dimensions:
    1. Relevance        : FAISS inner-product score distribution
    2. Redundancy       : Exact duplicate chunk IDs / content hashes
    3. Overlap          : Textual Jaccard token overlap & adjacent same-doc overlap
    4. Diversity        : Unique documents & sources
    5. Concentration    : Dominant document ratio
    6. Ordering         : Rank preservation & rank displacement
    7. Size & Tokens    : Character count & token approximation (chars // 4)
    8. Budget           : Utilization ratio & truncation state
    9. Evidence         : Evidence sufficiency vs baseline expected facts
"""
from __future__ import annotations

import hashlib
import logging
import re
import statistics
import time
from typing import Optional

from app.core.config import settings
from app.rag.analysis.context_snapshot import ContextSnapshot
from app.rag.analysis.quality_models import (
    AggregateQualityReport,
    BudgetMetrics,
    ContextQualityAnalysis,
    DiversityMetrics,
    EvidenceMetrics,
    OrderingMetrics,
    QualityCategory,
    RedundancyMetrics,
    RelevanceMetrics,
)
from app.retrieval.retrieval_models import RetrievedChunk

logger = logging.getLogger(__name__)


class ContextAnalyzer:
    """
    Analyzes context snapshots for quality, redundancy, size, and evidence.

    Usage::

        analyzer = ContextAnalyzer()
        analysis = analyzer.analyze_chunks(chunks, query="What is FastAPI?")
        print(analysis.categories)
        print(analysis.redundancy.duplicate_ratio)
    """

    def __init__(
        self,
        target_token_budget: Optional[int] = None,
        overlap_threshold: float = 0.50,
    ) -> None:
        self._target_token_budget = (
            target_token_budget
            if target_token_budget is not None
            else getattr(settings, "CONTEXT_MAX_OPTIMIZED_TOKENS", 2048)
        )
        self._overlap_threshold = overlap_threshold

    # ── Public interface ───────────────────────────────────────────────────────

    def analyze_snapshot(
        self,
        snapshot: ContextSnapshot,
        case_id: str = "",
        expected_facts: Optional[list[str]] = None,
        expected_source_ids: Optional[list[str]] = None,
        should_answer: bool = True,
    ) -> ContextQualityAnalysis:
        """
        Analyze a ContextSnapshot and return a detailed ContextQualityAnalysis.

        Args:
            snapshot            : ContextSnapshot instance.
            case_id             : Optional test case identifier.
            expected_facts      : List of canonical fact strings (from eval dataset).
            expected_source_ids : List of expected chunk IDs (from eval dataset).
            should_answer       : Expected answerability flag.

        Returns:
            ContextQualityAnalysis with all 9 analyzed dimensions.
        """
        t_start = time.perf_counter()
        chunks = snapshot.chunks

        # ── 1. Relevance ──────────────────────────────────────────────────────
        relevance = self._analyze_relevance(snapshot.retrieval_scores)

        # ── 2. Redundancy & Overlap ──────────────────────────────────────────
        redundancy = self._analyze_redundancy(chunks)

        # ── 3. Source Diversity & Concentration ──────────────────────────────
        diversity = self._analyze_diversity(chunks)

        # ── 4. Context Ordering ───────────────────────────────────────────────
        ordering = self._analyze_ordering(chunks)

        # ── 5. Size & Budget ──────────────────────────────────────────────────
        budget = self._analyze_budget(
            total_chars=snapshot.total_character_count,
            estimated_tokens=snapshot.estimated_token_count,
            chunk_count=snapshot.retrieved_chunk_count,
        )

        # ── 6. Evidence Sufficiency ───────────────────────────────────────────
        evidence = self._analyze_evidence(
            chunks=chunks,
            expected_facts=expected_facts,
            expected_source_ids=expected_source_ids,
            should_answer=should_answer,
        )

        # ── 7. Categorization ─────────────────────────────────────────────────
        categories = self._classify_categories(
            chunk_count=snapshot.retrieved_chunk_count,
            redundancy=redundancy,
            diversity=diversity,
            ordering=ordering,
            budget=budget,
            evidence=evidence,
            should_answer=should_answer,
        )

        duration_ms = (time.perf_counter() - t_start) * 1000

        return ContextQualityAnalysis(
            case_id=case_id,
            query=snapshot.query,
            chunk_count=snapshot.retrieved_chunk_count,
            categories=categories,
            relevance=relevance,
            redundancy=redundancy,
            diversity=diversity,
            ordering=ordering,
            budget=budget,
            evidence=evidence,
            analysis_duration_ms=duration_ms,
        )

    def analyze_chunks(
        self,
        chunks: list[RetrievedChunk],
        query: str = "",
        case_id: str = "",
        expected_facts: Optional[list[str]] = None,
        expected_source_ids: Optional[list[str]] = None,
        should_answer: bool = True,
    ) -> ContextQualityAnalysis:
        """Convenience helper: build snapshot from chunks and analyze it."""
        snapshot = ContextSnapshot.from_chunks(chunks, query=query)
        return self.analyze_snapshot(
            snapshot=snapshot,
            case_id=case_id,
            expected_facts=expected_facts,
            expected_source_ids=expected_source_ids,
            should_answer=should_answer,
        )

    def compute_aggregate(
        self, analyses: list[ContextQualityAnalysis]
    ) -> AggregateQualityReport:
        """
        Compute aggregate metrics over multiple ContextQualityAnalysis records.
        """
        if not analyses:
            return AggregateQualityReport(total_cases=0)

        total = len(analyses)
        good_count = sum(
            1 for a in analyses if QualityCategory.GOOD_CONTEXT in a.categories
        )
        redundant_count = sum(
            1 for a in analyses if QualityCategory.REDUNDANT_CONTEXT in a.categories
        )
        oversized_count = sum(
            1 for a in analyses if QualityCategory.OVERSIZED_CONTEXT in a.categories
        )
        insufficient_count = sum(
            1 for a in analyses if QualityCategory.INSUFFICIENT_CONTEXT in a.categories
        )
        concentrated_count = sum(
            1 for a in analyses if QualityCategory.CONCENTRATED_CONTEXT in a.categories
        )
        ordering_count = sum(
            1 for a in analyses if QualityCategory.ORDERING_ISSUE in a.categories
        )

        avg_chunks = statistics.mean(a.chunk_count for a in analyses)
        avg_docs = statistics.mean(a.diversity.unique_document_count for a in analyses)
        avg_sources = statistics.mean(a.diversity.unique_source_count for a in analyses)
        avg_dup_ratio = statistics.mean(a.redundancy.duplicate_ratio for a in analyses)
        avg_text_overlap = statistics.mean(a.redundancy.textual_overlap_avg for a in analyses)
        avg_dom_ratio = statistics.mean(a.diversity.dominant_document_ratio for a in analyses)

        avg_chars = statistics.mean(a.budget.total_characters for a in analyses)
        avg_tokens = statistics.mean(a.budget.estimated_tokens for a in analyses)

        utilization_values = [
            a.budget.utilization_ratio
            for a in analyses
            if a.budget.utilization_ratio is not None
        ]
        avg_budget_utilization = (
            statistics.mean(utilization_values) if utilization_values else None
        )

        truncation_rate = sum(1 for a in analyses if a.budget.truncated) / total

        evidence_vals = [
            a.evidence.evidence_sufficient
            for a in analyses
            if a.evidence.evidence_sufficient is not None
        ]
        evidence_sufficiency_rate = (
            sum(1 for v in evidence_vals if v) / len(evidence_vals)
            if evidence_vals
            else None
        )

        ordering_preserved_count = sum(
            1 for a in analyses if a.ordering.rank_order_preserved
        )
        ordering_preservation_rate = ordering_preserved_count / total

        return AggregateQualityReport(
            total_cases=total,
            good_context_count=good_count,
            redundant_context_count=redundant_count,
            oversized_context_count=oversized_count,
            insufficient_context_count=insufficient_count,
            concentrated_context_count=concentrated_count,
            ordering_issue_count=ordering_count,
            avg_chunks_per_case=avg_chunks,
            avg_unique_documents=avg_docs,
            avg_unique_sources=avg_sources,
            avg_duplicate_ratio=avg_dup_ratio,
            avg_textual_overlap=avg_text_overlap,
            avg_dominant_doc_ratio=avg_dom_ratio,
            avg_total_characters=avg_chars,
            avg_estimated_tokens=avg_tokens,
            avg_budget_utilization=avg_budget_utilization,
            truncation_rate=truncation_rate,
            evidence_sufficiency_rate=evidence_sufficiency_rate,
            ordering_preservation_rate=ordering_preservation_rate,
        )

    # ── Private diagnostic helpers ─────────────────────────────────────────────

    @staticmethod
    def _analyze_relevance(scores: list[float]) -> RelevanceMetrics:
        if not scores:
            return RelevanceMetrics()
        top_score = max(scores)
        min_score = min(scores)
        avg_score = statistics.mean(scores)
        median_score = statistics.median(scores)
        spread = top_score - min_score
        return RelevanceMetrics(
            top_score=top_score,
            min_score=min_score,
            avg_score=avg_score,
            median_score=median_score,
            score_spread=spread,
        )

    def _analyze_redundancy(self, chunks: list[RetrievedChunk]) -> RedundancyMetrics:
        if not chunks:
            return RedundancyMetrics()

        total = len(chunks)

        # 1. Exact duplicate chunk_ids or exact content hashes
        seen_ids: set[str] = set()
        seen_hashes: set[str] = set()
        duplicates = 0

        for c in chunks:
            is_dup = False
            if c.chunk_id and c.chunk_id in seen_ids:
                is_dup = True
            elif c.content:
                chash = hashlib.md5(c.content.strip().encode("utf-8")).hexdigest()
                if chash in seen_hashes:
                    is_dup = True
                else:
                    seen_hashes.add(chash)

            if c.chunk_id:
                seen_ids.add(c.chunk_id)

            if is_dup:
                duplicates += 1

        dup_ratio = duplicates / total if total > 0 else 0.0

        # 2. Textual overlap (Jaccard similarity on tokens across all chunk pairs)
        token_sets = [self._tokenize(c.content) for c in chunks if c.content]
        pair_overlaps = []
        adjacent_same_doc_overlaps = 0

        for i in range(len(token_sets)):
            for j in range(i + 1, len(token_sets)):
                overlap = self._jaccard_similarity(token_sets[i], token_sets[j])
                pair_overlaps.append(overlap)

        textual_overlap_avg = (
            statistics.mean(pair_overlaps) if pair_overlaps else 0.0
        )

        # 3. Check adjacent chunks from same document
        for i in range(len(chunks) - 1):
            c1, c2 = chunks[i], chunks[i + 1]
            if c1.document_id and c1.document_id == c2.document_id:
                t1 = self._tokenize(c1.content)
                t2 = self._tokenize(c2.content)
                if self._jaccard_similarity(t1, t2) > 0.3:
                    adjacent_same_doc_overlaps += 1

        return RedundancyMetrics(
            duplicate_chunk_count=duplicates,
            duplicate_ratio=dup_ratio,
            textual_overlap_avg=textual_overlap_avg,
            same_doc_adjacent_overlap_count=adjacent_same_doc_overlaps,
        )

    @staticmethod
    def _analyze_diversity(chunks: list[RetrievedChunk]) -> DiversityMetrics:
        if not chunks:
            return DiversityMetrics()

        doc_counts: dict[str, int] = {}
        source_names: set[str] = set()

        for c in chunks:
            doc_id = c.document_id or "unknown"
            doc_counts[doc_id] = doc_counts.get(doc_id, 0) + 1
            if c.document_name:
                source_names.add(c.document_name)

        max_doc_chunks = max(doc_counts.values()) if doc_counts else 0
        dominant_ratio = max_doc_chunks / len(chunks) if chunks else 0.0

        return DiversityMetrics(
            unique_document_count=len(doc_counts),
            unique_source_count=len(source_names) if source_names else len(doc_counts),
            dominant_document_ratio=dominant_ratio,
            chunks_per_document=doc_counts,
        )

    @staticmethod
    def _analyze_ordering(chunks: list[RetrievedChunk]) -> OrderingMetrics:
        if not chunks:
            return OrderingMetrics()

        # Check if rank sequence is strictly non-decreasing (1, 2, 3...)
        ranks = [c.rank for c in chunks if c.rank is not None]
        if not ranks:
            return OrderingMetrics()

        preserved = True
        max_displacement = 0
        for idx, rank in enumerate(ranks, start=1):
            displacement = abs(rank - idx)
            if displacement > max_displacement:
                max_displacement = displacement
            if rank < ranks[max(0, idx - 2)]:
                preserved = False

        return OrderingMetrics(
            rank_order_preserved=preserved,
            max_rank_displacement=max_displacement,
        )

    def _analyze_budget(
        self,
        total_chars: int,
        estimated_tokens: int,
        chunk_count: int,
    ) -> BudgetMetrics:
        configured_max = self._target_token_budget
        utilization: Optional[float] = None
        truncated = False

        if configured_max and configured_max > 0:
            utilization = estimated_tokens / configured_max
            truncated = estimated_tokens > configured_max

        return BudgetMetrics(
            total_characters=total_chars,
            estimated_tokens=estimated_tokens,
            configured_max_tokens=configured_max,
            utilization_ratio=utilization,
            truncated=truncated,
        )

    @staticmethod
    def _analyze_evidence(
        chunks: list[RetrievedChunk],
        expected_facts: Optional[list[str]],
        expected_source_ids: Optional[list[str]],
        should_answer: bool,
    ) -> EvidenceMetrics:
        if not should_answer:
            # Unanswerable cases: evidence is sufficient if empty retrieval
            return EvidenceMetrics(
                evidence_sufficient=len(chunks) == 0,
                fact_coverage=1.0 if len(chunks) == 0 else 0.0,
                source_coverage=1.0,
            )

        if not chunks:
            return EvidenceMetrics(
                evidence_sufficient=False,
                fact_coverage=0.0,
                source_coverage=0.0,
            )

        combined_text = " ".join(c.content.lower() for c in chunks if c.content)
        chunk_ids_retrieved = {c.chunk_id for c in chunks if c.chunk_id}

        # Fact coverage
        fact_cov = 1.0
        if expected_facts:
            matched_facts = sum(
                1 for fact in expected_facts if fact.lower().strip() in combined_text
            )
            fact_cov = matched_facts / len(expected_facts)

        # Source coverage
        src_cov = 1.0
        if expected_source_ids:
            matched_sources = sum(
                1 for sid in expected_source_ids if sid in chunk_ids_retrieved
            )
            src_cov = matched_sources / len(expected_source_ids)

        evidence_sufficient = fact_cov > 0.0 or src_cov > 0.0

        return EvidenceMetrics(
            evidence_sufficient=evidence_sufficient,
            fact_coverage=fact_cov,
            source_coverage=src_cov,
        )

    @staticmethod
    def _classify_categories(
        chunk_count: int,
        redundancy: RedundancyMetrics,
        diversity: DiversityMetrics,
        ordering: OrderingMetrics,
        budget: BudgetMetrics,
        evidence: EvidenceMetrics,
        should_answer: bool,
    ) -> list[QualityCategory]:
        categories: list[QualityCategory] = []

        if chunk_count == 0:
            categories.append(QualityCategory.INSUFFICIENT_CONTEXT)
            return categories

        if not should_answer and not evidence.evidence_sufficient:
            categories.append(QualityCategory.INSUFFICIENT_CONTEXT)

        if should_answer and evidence.evidence_sufficient is False:
            categories.append(QualityCategory.INSUFFICIENT_CONTEXT)

        if redundancy.duplicate_chunk_count > 0 or redundancy.textual_overlap_avg > 0.40:
            categories.append(QualityCategory.REDUNDANT_CONTEXT)

        if budget.truncated or (budget.utilization_ratio and budget.utilization_ratio > 1.0):
            categories.append(QualityCategory.OVERSIZED_CONTEXT)

        if diversity.dominant_document_ratio >= 0.75 and diversity.unique_document_count > 1:
            categories.append(QualityCategory.CONCENTRATED_CONTEXT)

        if not ordering.rank_order_preserved or ordering.max_rank_displacement > 2:
            categories.append(QualityCategory.ORDERING_ISSUE)

        if not categories:
            categories.append(QualityCategory.GOOD_CONTEXT)

        return categories

    @staticmethod
    def _tokenize(text: str) -> set[str]:
        if not text:
            return set()
        words = re.findall(r"\w+", text.lower())
        return {w for w in words if len(w) > 2}

    @staticmethod
    def _jaccard_similarity(set1: set[str], set2: set[str]) -> float:
        if not set1 or not set2:
            return 0.0
        intersection = len(set1 & set2)
        union = len(set1 | set2)
        return intersection / union if union > 0 else 0.0
