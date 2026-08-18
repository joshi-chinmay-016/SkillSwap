"""
Context Quality Models — Day 75 Part A1.

Provides data containers for Context Quality Analysis across 9 dimensions:
Relevance, Redundancy, Overlap, Source Diversity, Concentration, Ordering,
Size/Tokens, Budget/Truncation, Evidence Sufficiency.

Quality categories:
    GOOD_CONTEXT          : Well-bounded, non-redundant, relevant context.
    REDUNDANT_CONTEXT     : Contains exact duplicate or high textual overlap.
    OVERSIZED_CONTEXT     : Exceeds context token target.
    INSUFFICIENT_CONTEXT  : Empty or insufficient evidence context.
    CONCENTRATED_CONTEXT  : Single document dominates context (>80%).
    ORDERING_ISSUE        : High-relevance candidates displaced in context.
"""
from __future__ import annotations

import statistics
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class QualityCategory(str, Enum):
    """Classification categories for context quality analysis."""

    GOOD_CONTEXT = "good_context"
    REDUNDANT_CONTEXT = "redundant_context"
    OVERSIZED_CONTEXT = "oversized_context"
    INSUFFICIENT_CONTEXT = "insufficient_context"
    CONCENTRATED_CONTEXT = "concentrated_context"
    ORDERING_ISSUE = "ordering_issue"


@dataclass
class RelevanceMetrics:
    """FAISS similarity score analysis (inner product: higher = more relevant)."""

    top_score: Optional[float] = None
    min_score: Optional[float] = None
    avg_score: Optional[float] = None
    median_score: Optional[float] = None
    score_spread: Optional[float] = None  # top_score - min_score


@dataclass
class RedundancyMetrics:
    """Duplicate and textual overlap analysis."""

    duplicate_chunk_count: int = 0
    duplicate_ratio: float = 0.0          # duplicate_chunk_count / total_chunks
    textual_overlap_avg: float = 0.0        # Average Jaccard token overlap between chunks
    same_doc_adjacent_overlap_count: int = 0  # Adjacent chunks from same doc with overlap > 0.3


@dataclass
class DiversityMetrics:
    """Source and document concentration metrics."""

    unique_document_count: int = 0
    unique_source_count: int = 0
    dominant_document_ratio: float = 0.0   # max(chunks_from_doc) / total_chunks
    chunks_per_document: dict[str, int] = field(default_factory=dict)


@dataclass
class OrderingMetrics:
    """Ranking preservation metrics."""

    rank_order_preserved: bool = True
    max_rank_displacement: int = 0


@dataclass
class BudgetMetrics:
    """Character and estimated token budget utilization metrics."""

    total_characters: int = 0
    estimated_tokens: int = 0             # Approximate tokens = chars // 4
    configured_max_tokens: Optional[int] = None
    utilization_ratio: Optional[float] = None
    truncated: bool = False


@dataclass
class EvidenceMetrics:
    """Evidence sufficiency analysis using evaluation dataset baseline."""

    evidence_sufficient: Optional[bool] = None
    fact_coverage: Optional[float] = None
    source_coverage: Optional[float] = None


@dataclass
class ContextQualityAnalysis:
    """
    Per-case context quality analysis result combining all 9 quality dimensions.
    """

    case_id: str = ""
    query: str = ""
    chunk_count: int = 0
    categories: list[QualityCategory] = field(default_factory=list)

    relevance: RelevanceMetrics = field(default_factory=RelevanceMetrics)
    redundancy: RedundancyMetrics = field(default_factory=RedundancyMetrics)
    diversity: DiversityMetrics = field(default_factory=DiversityMetrics)
    ordering: OrderingMetrics = field(default_factory=OrderingMetrics)
    budget: BudgetMetrics = field(default_factory=BudgetMetrics)
    evidence: EvidenceMetrics = field(default_factory=EvidenceMetrics)

    analysis_duration_ms: float = 0.0

    def to_dict(self) -> dict:
        """Return JSON-serializable representation."""
        return {
            "case_id": self.case_id,
            "query_snippet": self.query[:100],
            "chunk_count": self.chunk_count,
            "categories": [c.value for c in self.categories],
            "relevance": {
                "top_score": self.relevance.top_score,
                "min_score": self.relevance.min_score,
                "avg_score": self.relevance.avg_score,
                "median_score": self.relevance.median_score,
                "score_spread": self.relevance.score_spread,
            },
            "redundancy": {
                "duplicate_chunk_count": self.redundancy.duplicate_chunk_count,
                "duplicate_ratio": self.redundancy.duplicate_ratio,
                "textual_overlap_avg": self.redundancy.textual_overlap_avg,
                "same_doc_adjacent_overlap_count": self.redundancy.same_doc_adjacent_overlap_count,
            },
            "diversity": {
                "unique_document_count": self.diversity.unique_document_count,
                "unique_source_count": self.diversity.unique_source_count,
                "dominant_document_ratio": self.diversity.dominant_document_ratio,
            },
            "ordering": {
                "rank_order_preserved": self.ordering.rank_order_preserved,
                "max_rank_displacement": self.ordering.max_rank_displacement,
            },
            "budget": {
                "total_characters": self.budget.total_characters,
                "estimated_tokens": self.budget.estimated_tokens,
                "configured_max_tokens": self.budget.configured_max_tokens,
                "utilization_ratio": self.budget.utilization_ratio,
                "truncated": self.budget.truncated,
            },
            "evidence": {
                "evidence_sufficient": self.evidence.evidence_sufficient,
                "fact_coverage": self.evidence.fact_coverage,
                "source_coverage": self.evidence.source_coverage,
            },
            "analysis_duration_ms": self.analysis_duration_ms,
        }


@dataclass
class AggregateQualityReport:
    """Summary of context quality analysis over multiple evaluated cases."""

    total_cases: int = 0
    good_context_count: int = 0
    redundant_context_count: int = 0
    oversized_context_count: int = 0
    insufficient_context_count: int = 0
    concentrated_context_count: int = 0
    ordering_issue_count: int = 0

    avg_chunks_per_case: float = 0.0
    avg_unique_documents: float = 0.0
    avg_unique_sources: float = 0.0
    avg_duplicate_ratio: float = 0.0
    avg_textual_overlap: float = 0.0
    avg_dominant_doc_ratio: float = 0.0

    avg_total_characters: float = 0.0
    avg_estimated_tokens: float = 0.0
    avg_budget_utilization: Optional[float] = None
    truncation_rate: float = 0.0

    evidence_sufficiency_rate: Optional[float] = None
    ordering_preservation_rate: float = 1.0

    def to_dict(self) -> dict:
        return {
            "total_cases": self.total_cases,
            "category_counts": {
                "good_context": self.good_context_count,
                "redundant_context": self.redundant_context_count,
                "oversized_context": self.oversized_context_count,
                "insufficient_context": self.insufficient_context_count,
                "concentrated_context": self.concentrated_context_count,
                "ordering_issue": self.ordering_issue_count,
            },
            "averages": {
                "chunks_per_case": self.avg_chunks_per_case,
                "unique_documents": self.avg_unique_documents,
                "unique_sources": self.avg_unique_sources,
                "duplicate_ratio": self.avg_duplicate_ratio,
                "textual_overlap": self.avg_textual_overlap,
                "dominant_doc_ratio": self.avg_dominant_doc_ratio,
                "total_characters": self.avg_total_characters,
                "estimated_tokens": self.avg_estimated_tokens,
                "budget_utilization": self.avg_budget_utilization,
            },
            "rates": {
                "truncation_rate": self.truncation_rate,
                "evidence_sufficiency_rate": self.evidence_sufficiency_rate,
                "ordering_preservation_rate": self.ordering_preservation_rate,
            },
        }

    def format_human_readable(self) -> str:
        def fmt_pct(val: Optional[float]) -> str:
            return f"{val * 100:.1f}%" if val is not None else "N/A"

        lines = [
            "Context Quality Analysis Summary",
            "-" * 45,
            f"Total Analyzed Cases:        {self.total_cases}",
            f"  GOOD CONTEXT:              {self.good_context_count}",
            f"  REDUNDANT CONTEXT:         {self.redundant_context_count}",
            f"  OVERSIZED CONTEXT:         {self.oversized_context_count}",
            f"  INSUFFICIENT CONTEXT:      {self.insufficient_context_count}",
            f"  CONCENTRATED CONTEXT:      {self.concentrated_context_count}",
            f"  ORDERING ISSUES:           {self.ordering_issue_count}",
            "",
            "Averages & Signals:",
            f"  Avg Chunks per Case:       {self.avg_chunks_per_case:.1f}",
            f"  Avg Unique Documents:      {self.avg_unique_documents:.1f}",
            f"  Avg Duplicate Ratio:       {fmt_pct(self.avg_duplicate_ratio)}",
            f"  Avg Textual Overlap:       {fmt_pct(self.avg_textual_overlap)}",
            f"  Avg Dominant Doc Ratio:    {fmt_pct(self.avg_dominant_doc_ratio)}",
            f"  Avg Estimated Tokens:      {self.avg_estimated_tokens:.1f}",
            f"  Avg Budget Utilization:    {fmt_pct(self.avg_budget_utilization)}",
            "",
            "Rates:",
            f"  Truncation Rate:           {fmt_pct(self.truncation_rate)}",
            f"  Evidence Sufficiency Rate: {fmt_pct(self.evidence_sufficiency_rate)}",
            f"  Ordering Preservation Rate:{fmt_pct(self.ordering_preservation_rate)}",
        ]
        return "\n".join(lines)
