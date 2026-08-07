"""
ChunkFactory — Strategy registry and selector (Day 68 Part A1).

New strategies can be registered without modifying any existing code:

    ChunkFactory.register(MyStrategy())

Usage:
    strategy = ChunkFactory.get_strategy("md")
    chunks = strategy.chunk(text, chunk_size=800, chunk_overlap=150)

The factory falls back to RecursiveChunkStrategy for any unrecognised type.
"""
from __future__ import annotations

import logging

from parsers.chunking.chunk_strategy import ChunkStrategy
from parsers.chunking.recursive_chunk_strategy import RecursiveChunkStrategy

logger = logging.getLogger(__name__)

# ── Strategy registry ─────────────────────────────────────────────────────────
# Maps lowercase document type → strategy instance.
# RecursiveChunkStrategy is the universal fallback (supports any type).

_STRATEGY_REGISTRY: list[ChunkStrategy] = [
    RecursiveChunkStrategy(),
]


class ChunkFactory:
    """
    Selects the most appropriate chunking strategy for a given document type.

    Design:
        - Strategies are checked in registration order.
        - The first strategy whose `supports()` returns True is used.
        - RecursiveChunkStrategy is always the last entry (universal fallback).
        - Adding a new strategy requires only `ChunkFactory.register(instance)`.
    """

    @classmethod
    def register(cls, strategy: ChunkStrategy) -> None:
        """
        Register a new strategy.

        The new strategy is inserted BEFORE the universal fallback so it takes
        priority over RecursiveChunkStrategy for types it supports.

        Args:
            strategy: A concrete ChunkStrategy instance.
        """
        # Insert before the last entry (the recursive fallback)
        _STRATEGY_REGISTRY.insert(len(_STRATEGY_REGISTRY) - 1, strategy)
        logger.info(
            "ChunkFactory — registered strategy '%s' v%s",
            strategy.name,
            strategy.version,
        )

    @classmethod
    def get_strategy(cls, document_type: str) -> ChunkStrategy:
        """
        Return the best strategy for the given document type.

        Args:
            document_type: Lowercase file extension without dot (e.g. 'pdf', 'md').

        Returns:
            A ChunkStrategy instance. Always returns at least RecursiveChunkStrategy.
        """
        dtype = (document_type or "txt").lower().strip().lstrip(".")
        for strategy in _STRATEGY_REGISTRY:
            if strategy.supports(dtype):
                logger.debug(
                    "ChunkFactory — selected strategy '%s' for type '%s'",
                    strategy.name,
                    dtype,
                )
                return strategy

        # Guaranteed fallback (should never reach here since recursive supports all)
        logger.warning(
            "ChunkFactory — no strategy found for '%s', falling back to recursive",
            dtype,
        )
        return RecursiveChunkStrategy()

    @classmethod
    def list_strategies(cls) -> list[str]:
        """Return names of all registered strategies in priority order."""
        return [s.name for s in _STRATEGY_REGISTRY]
