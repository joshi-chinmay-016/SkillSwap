"""
chunk_integrity_validator — Validates persisted Chunk sets (Day 68 Part A2).

Runs AFTER chunks are fetched from the database (or before bulk insert) to
guarantee the stored chunk set is internally consistent.

Validation checks:
    1. Ordering: chunk_index must be 0, 1, 2, … with no gaps.
    2. Offset correctness: end_offset >= start_offset for each chunk.
    3. Offset monotonicity: start_offsets must be non-decreasing.
    4. Duplicate detection: no two chunks with identical text fingerprints.
    5. Strategy consistency: all chunks must share the same strategy name.
    6. Metadata completeness: estimated_tokens > 0, chunk_size > 0.

This module is pure Python — no database access.
"""
from __future__ import annotations

import hashlib
from typing import Any


class ChunkIntegrityError(Exception):
    """Raised when a persisted chunk set fails integrity validation."""

    def __init__(self, errors: list[str]) -> None:
        self.errors = errors
        super().__init__(
            f"Chunk integrity validation failed with {len(errors)} error(s): {errors[0]}"
        )


def validate_chunk_set(
    chunks: list[Any],  # list of Chunk ORM objects or ChunkData
    *,
    raise_on_error: bool = False,
) -> list[str]:
    """
    Validate a list of Chunk ORM objects (or ChunkData) for integrity.

    Works with both ORM Chunk objects and ChunkData dataclass instances —
    both expose the same attribute names.

    Args:
        chunks        : Ordered list of chunk objects to validate.
        raise_on_error: If True, raise ChunkIntegrityError on any failure.

    Returns:
        List of human-readable error strings.  Empty = valid.

    Raises:
        ChunkIntegrityError: If raise_on_error=True and errors are found.
    """
    errors: list[str] = []

    if not chunks:
        return errors

    # ── 1. Ordering ───────────────────────────────────────────────────────────
    for expected, chunk in enumerate(chunks):
        if chunk.chunk_index != expected:
            errors.append(
                f"[ordering] chunk_index={chunk.chunk_index} at position {expected} "
                f"(expected {expected})"
            )

    # ── 2. Offset correctness ──────────────────────────────────────────────────
    for chunk in chunks:
        if chunk.end_offset < chunk.start_offset:
            errors.append(
                f"[offset] Chunk {chunk.chunk_index}: end_offset ({chunk.end_offset}) "
                f"< start_offset ({chunk.start_offset})"
            )

    # ── 3. Offset monotonicity ────────────────────────────────────────────────
    for i in range(1, len(chunks)):
        if chunks[i].start_offset < chunks[i - 1].start_offset:
            errors.append(
                f"[monotonicity] Chunk {chunks[i].chunk_index} start_offset "
                f"({chunks[i].start_offset}) < chunk {chunks[i-1].chunk_index} "
                f"start_offset ({chunks[i-1].start_offset})"
            )

    # ── 4. Duplicate detection ─────────────────────────────────────────────────
    seen_fingerprints: set[str] = set()
    for chunk in chunks:
        fp = _fingerprint(chunk.chunk_text)
        if fp in seen_fingerprints:
            errors.append(
                f"[duplicate] Chunk {chunk.chunk_index} has identical text fingerprint "
                f"to a previously seen chunk."
            )
        seen_fingerprints.add(fp)

    # ── 5. Strategy consistency ────────────────────────────────────────────────
    strategies = {c.strategy for c in chunks}
    if len(strategies) > 1:
        errors.append(
            f"[strategy] Inconsistent strategies in chunk set: {sorted(strategies)}. "
            "All chunks in a set must share the same strategy."
        )

    # ── 6. Metadata completeness ──────────────────────────────────────────────
    for chunk in chunks:
        if chunk.estimated_tokens <= 0 and chunk.chunk_text.strip():
            errors.append(
                f"[metadata] Chunk {chunk.chunk_index}: estimated_tokens="
                f"{chunk.estimated_tokens} for non-empty text."
            )
        if chunk.chunk_size <= 0:
            errors.append(
                f"[metadata] Chunk {chunk.chunk_index}: chunk_size="
                f"{chunk.chunk_size} must be > 0."
            )

    if raise_on_error and errors:
        raise ChunkIntegrityError(errors)

    return errors


def assert_chunk_set_valid(chunks: list[Any]) -> None:
    """
    Assert integrity of a chunk set, raising ChunkIntegrityError if invalid.

    Convenience wrapper for use in ChunkService.

    Args:
        chunks: List of Chunk ORM objects or ChunkData.

    Raises:
        ChunkIntegrityError: If any integrity check fails.
    """
    validate_chunk_set(chunks, raise_on_error=True)


# ── Internal helpers ──────────────────────────────────────────────────────────

def _fingerprint(text: str) -> str:
    """Return a short SHA-256 hex digest for duplicate detection."""
    return hashlib.sha256((text or "").encode("utf-8")).hexdigest()[:16]
