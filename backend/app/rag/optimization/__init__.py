"""
RAG Context Optimization Package — Day 75 Part A2.

Provides controlled Context Optimization over retrieved chunks before context
construction.

Components:
    ContextOptimizer          : Abstract interface
    DefaultContextOptimizer   : Production 4-stage optimization pass
    OptimizationReason        : Enum of removal reasons
    OptimizedChunkRecord      : Audit record per processed chunk
    ContextOptimizationResult : Summary result with original & optimized chunk lists
"""
from app.rag.optimization.context_optimizer import (
    ContextOptimizer,
    DefaultContextOptimizer,
)
from app.rag.optimization.optimizer_models import (
    ContextOptimizationResult,
    OptimizationReason,
    OptimizedChunkRecord,
)

__all__ = [
    "ContextOptimizer",
    "DefaultContextOptimizer",
    "OptimizationReason",
    "OptimizedChunkRecord",
    "ContextOptimizationResult",
]
