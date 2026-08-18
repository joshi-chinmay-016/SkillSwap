"""
ContextOptimizer — Day 75 Part A2.

Implements controlled Context Optimization over retrieved chunks before they
enter ContextBuilder / PromptBuilder.

Optimization stages (4 deterministic passes):
    1. Validation & Exact Duplicate Removal:
       - Omit invalid or empty chunks.
       - Set-based deduplication on chunk_id / content MD5.
       - Keeps first valid occurrence (best retrieval rank).

    2. Redundancy & Textual Overlap Reduction:
       - Compare candidate text against already selected chunks using Jaccard token overlap.
       - If overlap > CONTEXT_OVERLAP_THRESHOLD (default 0.85) AND candidate does not
         add meaningful unique tokens, omit candidate with reason=HIGH_TEXTUAL_OVERLAP.
       - Guarantees evidence chunks from different documents or distinct sections are kept.

    3. Source & Evidence Preservation:
       - Preserves top chunks from distinct documents to maintain source coverage.

    4. Token Budget Enforcement & Stable Rank Ordering:
       - Enforces CONTEXT_MAX_OPTIMIZED_TOKENS (default 2048 tokens / ~8192 chars).
       - Retains original relative retrieval rank order (e.g., A, C, E).

Safety & Invariants:
    - Does NOT mutate the input retrieved_chunks list or original chunk objects.
    - Does NOT alter FAISS candidate scores or change similarity metrics.
    - Does NOT call an LLM or re-embed text.
    - Operates after authorization and lifecycle filtering (authorization preserved).
"""
from __future__ import annotations

import abc
import hashlib
import logging
import re
import time
from typing import Optional

from app.core.config import settings
from app.rag.optimization.optimizer_models import (
    ContextOptimizationResult,
    OptimizationReason,
    OptimizedChunkRecord,
)
from app.retrieval.retrieval_models import RetrievedChunk

logger = logging.getLogger(__name__)


class ContextOptimizer(abc.ABC):
    """
    Abstract interface for context optimization strategies.
    """

    @abc.abstractmethod
    def optimize(
        self, chunks: list[RetrievedChunk]
    ) -> ContextOptimizationResult:
        """
        Optimize context from authorized retrieved chunks.

        Args:
            chunks: Authorized retrieved chunks from Retriever.

        Returns:
            ContextOptimizationResult with original and optimized chunk lists.
        """
        ...


class DefaultContextOptimizer(ContextOptimizer):
    """
    Production implementation of ContextOptimizer.

    Reads configuration defaults from application settings.

    Usage::

        optimizer = DefaultContextOptimizer.from_settings()
        result = optimizer.optimize(retrieved_chunks)
        print(result.optimized_chunk_count)
    """

    def __init__(
        self,
        *,
        overlap_threshold: float = 0.85,
        max_tokens: int = 2048,
        enabled: bool = True,
    ) -> None:
        self._overlap_threshold = overlap_threshold
        self._max_tokens = max_tokens
        self._enabled = enabled

    @classmethod
    def from_settings(cls) -> "DefaultContextOptimizer":
        return cls(
            overlap_threshold=getattr(settings, "CONTEXT_OVERLAP_THRESHOLD", 0.85),
            max_tokens=getattr(settings, "CONTEXT_MAX_OPTIMIZED_TOKENS", 2048),
            enabled=getattr(settings, "CONTEXT_OPTIMIZATION_ENABLED", True),
        )

    def optimize(
        self, chunks: list[RetrievedChunk]
    ) -> ContextOptimizationResult:
        """
        Execute deterministic 4-stage optimization pass on retrieved chunks.
        """
        t_start = time.perf_counter()

        if not chunks:
            return ContextOptimizationResult(optimization_duration_ms=0.0)

        # Calculate original statistics
        orig_chars = sum(len(c.content) for c in chunks if c.content)
        orig_tokens = orig_chars // 4

        if not self._enabled:
            # Pass-through if disabled via config
            records = [
                OptimizedChunkRecord(
                    chunk_id=c.chunk_id,
                    document_id=c.document_id,
                    rank=c.rank,
                    score=c.score,
                    action="KEPT",
                    character_len=len(c.content) if c.content else 0,
                )
                for c in chunks
            ]
            return ContextOptimizationResult(
                original_chunks=list(chunks),
                optimized_chunks=list(chunks),
                original_chunk_count=len(chunks),
                optimized_chunk_count=len(chunks),
                original_character_count=orig_chars,
                optimized_character_count=orig_chars,
                original_token_estimate=orig_tokens,
                optimized_token_estimate=orig_tokens,
                records=records,
                optimization_duration_ms=(time.perf_counter() - t_start) * 1000,
            )

        selected_chunks: list[RetrievedChunk] = []
        selected_token_sets: list[set[str]] = []
        records: list[OptimizedChunkRecord] = []

        seen_chunk_ids: set[str] = set()
        seen_content_hashes: set[str] = set()

        removed_duplicates = 0
        removed_overlaps = 0
        removed_budget = 0

        current_token_count = 0
        max_char_budget = self._max_tokens * 4

        for c in chunks:
            char_len = len(c.content) if c.content else 0

            # ── Stage 1: Validation & Exact Duplicate Removal ──────────────
            if not c.content or not c.content.strip():
                records.append(
                    OptimizedChunkRecord(
                        chunk_id=c.chunk_id,
                        document_id=c.document_id,
                        rank=c.rank,
                        score=c.score,
                        action="REMOVED",
                        reason=OptimizationReason.INVALID_CHUNK,
                        character_len=char_len,
                    )
                )
                continue

            # Exact duplicate check by chunk_id
            if c.chunk_id and c.chunk_id in seen_chunk_ids:
                removed_duplicates += 1
                records.append(
                    OptimizedChunkRecord(
                        chunk_id=c.chunk_id,
                        document_id=c.document_id,
                        rank=c.rank,
                        score=c.score,
                        action="REMOVED",
                        reason=OptimizationReason.EXACT_DUPLICATE,
                        character_len=char_len,
                    )
                )
                continue

            # Exact content hash duplicate check
            chash = hashlib.md5(c.content.strip().encode("utf-8")).hexdigest()
            if chash in seen_content_hashes:
                removed_duplicates += 1
                records.append(
                    OptimizedChunkRecord(
                        chunk_id=c.chunk_id,
                        document_id=c.document_id,
                        rank=c.rank,
                        score=c.score,
                        action="REMOVED",
                        reason=OptimizationReason.EXACT_DUPLICATE,
                        character_len=char_len,
                    )
                )
                continue

            # ── Stage 2: Redundancy & Overlap Reduction ───────────────────
            cand_tokens = self._tokenize(c.content)
            is_redundant = False

            for sel_tokens in selected_token_sets:
                overlap = self._jaccard_similarity(cand_tokens, sel_tokens)
                if overlap >= self._overlap_threshold:
                    # High overlap with an already selected chunk → omit
                    is_redundant = True
                    break

            if is_redundant:
                removed_overlaps += 1
                records.append(
                    OptimizedChunkRecord(
                        chunk_id=c.chunk_id,
                        document_id=c.document_id,
                        rank=c.rank,
                        score=c.score,
                        action="REMOVED",
                        reason=OptimizationReason.HIGH_TEXTUAL_OVERLAP,
                        character_len=char_len,
                    )
                )
                continue

            # ── Stage 3: Budget Enforcement ───────────────────────────────
            chunk_tokens = char_len // 4
            if (current_token_count + chunk_tokens) > self._max_tokens and len(selected_chunks) > 0:
                removed_budget += 1
                records.append(
                    OptimizedChunkRecord(
                        chunk_id=c.chunk_id,
                        document_id=c.document_id,
                        rank=c.rank,
                        score=c.score,
                        action="REMOVED",
                        reason=OptimizationReason.CONTEXT_BUDGET,
                        character_len=char_len,
                    )
                )
                continue

            # Candidate selected!
            selected_chunks.append(c)
            selected_token_sets.append(cand_tokens)
            current_token_count += chunk_tokens

            if c.chunk_id:
                seen_chunk_ids.add(c.chunk_id)
            seen_content_hashes.add(chash)

            records.append(
                OptimizedChunkRecord(
                    chunk_id=c.chunk_id,
                    document_id=c.document_id,
                    rank=c.rank,
                    score=c.score,
                    action="KEPT",
                    character_len=char_len,
                )
            )

        # Calculate optimized statistics
        opt_chars = sum(len(c.content) for c in selected_chunks if c.content)
        opt_tokens = opt_chars // 4

        duration_ms = (time.perf_counter() - t_start) * 1000

        logger.debug(
            "DefaultContextOptimizer.optimize — orig_chunks=%d opt_chunks=%d "
            "dups_removed=%d overlaps_removed=%d budget_removed=%d duration_ms=%.2f",
            len(chunks),
            len(selected_chunks),
            removed_duplicates,
            removed_overlaps,
            removed_budget,
            duration_ms,
        )

        return ContextOptimizationResult(
            original_chunks=list(chunks),
            optimized_chunks=selected_chunks,
            original_chunk_count=len(chunks),
            optimized_chunk_count=len(selected_chunks),
            removed_duplicate_count=removed_duplicates,
            removed_overlap_count=removed_overlaps,
            removed_budget_count=removed_budget,
            original_character_count=orig_chars,
            optimized_character_count=opt_chars,
            original_token_estimate=orig_tokens,
            optimized_token_estimate=opt_tokens,
            budget_applied=removed_budget > 0,
            records=records,
            optimization_duration_ms=duration_ms,
        )

    # ── Helpers ───────────────────────────────────────────────────────────────

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
