"""
RAG Context Analysis Package — Day 75 Part A1.

Diagnostic layer for measuring RAG context quality, redundancy, diversity,
budget utilization, and evidence coverage.

Components:
    ContextSnapshot         : Structured snapshot of context before LLM
    ContextAnalyzer         : Diagnostic engine analyzing 9 context dimensions
    QualityCategory         : Enum of context quality categories
    RelevanceMetrics        : Score distribution metrics
    RedundancyMetrics       : Duplicates and textual overlap metrics
    DiversityMetrics        : Document & source concentration metrics
    OrderingMetrics         : Rank preservation metrics
    BudgetMetrics           : Tokens, characters, utilization metrics
    EvidenceMetrics         : Evidence sufficiency vs dataset baselines
    ContextQualityAnalysis  : Per-case diagnostic result
    AggregateQualityReport  : Summary statistics over multiple analyzed cases
"""
from app.rag.analysis.context_analyzer import ContextAnalyzer
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

__all__ = [
    "ContextSnapshot",
    "ContextAnalyzer",
    "QualityCategory",
    "RelevanceMetrics",
    "RedundancyMetrics",
    "DiversityMetrics",
    "OrderingMetrics",
    "BudgetMetrics",
    "EvidenceMetrics",
    "ContextQualityAnalysis",
    "AggregateQualityReport",
]
