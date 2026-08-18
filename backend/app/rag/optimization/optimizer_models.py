"""
Context Optimizer Models — Day 75 Part A2.

Typed data containers for the controlled Context Optimization layer.

Models:
    OptimizationReason         : Enum describing why a chunk was removed.
    OptimizedChunkRecord       : Audit record for each chunk processed by ContextOptimizer.
    ContextOptimizationResult  : Output produced by ContextOptimizer containing the
                                 optimized chunk list and audit metrics.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

from app.retrieval.retrieval_models import RetrievedChunk


class OptimizationReason(str, Enum):
    """Reasons why a candidate chunk was omitted by ContextOptimizer."""

    EXACT_DUPLICATE = "exact_duplicate"
    HIGH_TEXTUAL_OVERLAP = "high_textual_overlap"
    CONTEXT_BUDGET = "context_budget"
    INVALID_CHUNK = "invalid_chunk"


@dataclass
class OptimizedChunkRecord:
    """
    Audit log entry for a single retrieved chunk processed during optimization.

    Fields:
        chunk_id       : PostgreSQL Chunk UUID.
        document_id    : Parent Document UUID.
        rank           : Original 1-based retrieval rank.
        score          : Original FAISS inner-product score.
        action         : "KEPT" or "REMOVED".
        reason         : OptimizationReason if REMOVED.
        character_len  : Length of content string.
    """

    chunk_id: str
    document_id: str
    rank: int
    score: float
    action: str  # "KEPT" | "REMOVED"
    reason: Optional[OptimizationReason] = None
    character_len: int = 0


@dataclass
class ContextOptimizationResult:
    """
    Result returned by ContextOptimizer.

    Fields:
        original_chunks             : Immutable list of raw retrieved chunks (for comparison).
        optimized_chunks            : Derived list of optimized, non-redundant chunks.
        original_chunk_count        : Count of retrieved chunks before optimization.
        optimized_chunk_count       : Count of chunks selected after optimization.
        removed_duplicate_count     : Count of exact duplicate chunks removed.
        removed_overlap_count       : Count of high-overlap redundant chunks removed.
        removed_budget_count        : Count of chunks omitted to satisfy context budget.
        original_character_count    : Character sum before optimization.
        optimized_character_count   : Character sum after optimization.
        original_token_estimate     : Estimated tokens (chars // 4) before optimization.
        optimized_token_estimate    : Estimated tokens (chars // 4) after optimization.
        budget_applied              : True if context budget was enforced.
        records                     : Per-chunk audit logs.
        optimization_duration_ms    : Time taken in milliseconds to optimize context.
    """

    original_chunks: list[RetrievedChunk] = field(default_factory=list)
    optimized_chunks: list[RetrievedChunk] = field(default_factory=list)

    original_chunk_count: int = 0
    optimized_chunk_count: int = 0

    removed_duplicate_count: int = 0
    removed_overlap_count: int = 0
    removed_budget_count: int = 0

    original_character_count: int = 0
    optimized_character_count: int = 0

    original_token_estimate: int = 0
    optimized_token_estimate: int = 0

    budget_applied: bool = False
    records: list[OptimizedChunkRecord] = field(default_factory=list)
    optimization_duration_ms: float = 0.0

    def to_dict(self) -> dict:
        """Return a JSON-serializable dictionary representation."""
        return {
            "original_chunk_count": self.original_chunk_count,
            "optimized_chunk_count": self.optimized_chunk_count,
            "removed_duplicate_count": self.removed_duplicate_count,
            "removed_overlap_count": self.removed_overlap_count,
            "removed_budget_count": self.removed_budget_count,
            "original_character_count": self.original_character_count,
            "optimized_character_count": self.optimized_character_count,
            "original_token_estimate": self.original_token_estimate,
            "optimized_token_estimate": self.optimized_token_estimate,
            "budget_applied": self.budget_applied,
            "optimization_duration_ms": self.optimization_duration_ms,
            "records": [
                {
                    "chunk_id": r.chunk_id,
                    "document_id": r.document_id,
                    "rank": r.rank,
                    "score": r.score,
                    "action": r.action,
                    "reason": r.reason.value if r.reason else None,
                }
                for r in self.records
            ],
        }
