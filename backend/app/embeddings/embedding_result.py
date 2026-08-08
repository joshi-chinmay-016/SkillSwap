"""
EmbeddingResult — Structured output of a single embedding operation (Day 69 Part A1).

This data class is the boundary object between the embedding generation layer
(EmbeddingProvider) and the persistence layer (EmbeddingRepository).

The vector field is included here for transport between layers but is NEVER
logged, serialised into API responses, or exposed to the frontend.

Consumers:
    EmbeddingService  → receives EmbeddingResult from the provider pipeline
    EmbeddingRepository → persists the result to the database

Future:
    VectorStorageAdapter (Day 70) → consumes EmbeddingResult for indexing
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone


# ── Status enum values (mirrors EmbeddingStatus in models/embedding.py) ───────
# Defined here as constants to avoid a circular import — the model imports
# this module for the status string values, not the other way around.

EMBEDDING_STATUS_PENDING = "PENDING"
EMBEDDING_STATUS_PROCESSING = "PROCESSING"
EMBEDDING_STATUS_READY = "READY"
EMBEDDING_STATUS_FAILED = "FAILED"
EMBEDDING_STATUS_ARCHIVED = "ARCHIVED"


@dataclass
class EmbeddingResult:
    """
    Structured output produced for one chunk by the embedding pipeline.

    Fields:
        chunk_id         : UUID of the source Chunk.
        vector           : The embedding vector (list of floats).
                           Never log this field.
        provider         : Short provider name (e.g. 'gemini').
        model_name       : Canonical model identifier (e.g. 'text-embedding-004').
        model_version    : Provider-level model version string (e.g. 'v1').
        dimension        : Length of the vector.
        embedding_version: Application-level version (from settings).
        status           : One of the EMBEDDING_STATUS_* constants.
        error_message    : Human-readable error summary (if status=FAILED).
        error_category   : Normalised error type (e.g. 'rate_limit', 'timeout').
        generated_at     : UTC timestamp of generation.
        duration_ms      : Time taken for the provider call, in milliseconds.
    """

    chunk_id: str
    vector: list[float]
    provider: str
    model_name: str
    model_version: str
    dimension: int
    embedding_version: int
    status: str = EMBEDDING_STATUS_READY

    # ── Failure metadata (populated when status=FAILED) ───────────────────────
    error_message: str | None = None
    error_category: str | None = None

    # ── Observability ─────────────────────────────────────────────────────────
    generated_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    duration_ms: float = 0.0

    # ── Optional job/batch tracing ─────────────────────────────────────────────
    job_id: str | None = None
    batch_id: str | None = None

    def __post_init__(self) -> None:
        if self.dimension == 0 and self.vector:
            self.dimension = len(self.vector)

    @property
    def is_valid(self) -> bool:
        """True if this result represents a successfully generated embedding."""
        return self.status == EMBEDDING_STATUS_READY and bool(self.vector)

    def safe_repr(self) -> str:
        """
        Return a log-safe string representation.

        The vector is deliberately excluded to prevent accidental logging of
        potentially sensitive embedding data.
        """
        return (
            f"EmbeddingResult("
            f"chunk_id={self.chunk_id!r}, "
            f"provider={self.provider!r}, "
            f"model={self.model_name!r}, "
            f"dim={self.dimension}, "
            f"status={self.status!r}, "
            f"duration_ms={self.duration_ms:.1f}"
            f")"
        )

    def __repr__(self) -> str:
        # Never print the vector in repr — only safe metadata.
        return self.safe_repr()


@dataclass
class BatchEmbeddingResult:
    """
    Aggregated result for one batch of chunks.

    Contains individual EmbeddingResult objects and batch-level statistics.
    """

    batch_index: int
    results: list[EmbeddingResult] = field(default_factory=list)
    job_id: str | None = None
    batch_id: str | None = None

    @property
    def total(self) -> int:
        return len(self.results)

    @property
    def ready_count(self) -> int:
        return sum(1 for r in self.results if r.status == EMBEDDING_STATUS_READY)

    @property
    def failed_count(self) -> int:
        return sum(1 for r in self.results if r.status == EMBEDDING_STATUS_FAILED)

    @property
    def average_duration_ms(self) -> float:
        if not self.results:
            return 0.0
        return sum(r.duration_ms for r in self.results) / len(self.results)

    def __repr__(self) -> str:
        return (
            f"BatchEmbeddingResult("
            f"batch_index={self.batch_index}, "
            f"total={self.total}, "
            f"ready={self.ready_count}, "
            f"failed={self.failed_count}"
            f")"
        )
