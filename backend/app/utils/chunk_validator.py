"""
chunk_validator — In-memory ChunkData validation (Day 68 Part A1).

Validates a list of ChunkData objects produced by a chunking strategy
BEFORE they are handed off to the persistence layer.

Validation rules:
    1. Non-empty text (each chunk must have printable content)
    2. Chunk size limits (no chunk may exceed 2× the configured chunk_size)
    3. Ordering (chunk_index must be 0, 1, 2, … with no gaps)
    4. Offset monotonicity (start_offsets must be non-decreasing)
    5. Duplicate text prevention (no two chunks may have identical full text)
    6. Token sanity (estimated_tokens must be > 0 for non-empty chunks)

This module is stateless — all functions are pure.
"""
from __future__ import annotations

import hashlib
from typing import Optional

from parsers.chunking.chunk_strategy import ChunkData


class ChunkValidationError(Exception):
    """Raised when a chunk set fails validation."""

    def __init__(self, errors: list[str]) -> None:
        self.errors = errors
        super().__init__(f"Chunk validation failed with {len(errors)} error(s): {errors[0]}")


def validate_chunks(
    chunks: list[ChunkData],
    *,
    max_chunk_size_multiplier: float = 2.0,
    raise_on_error: bool = False,
) -> list[str]:
    """
    Validate a list of ChunkData objects.

    Args:
        chunks                   : Output from a ChunkStrategy.chunk() call.
        max_chunk_size_multiplier: Chunks larger than this multiple of their
                                   configured chunk_size are flagged.
        raise_on_error           : If True, raise ChunkValidationError on first
                                   failure instead of returning errors.

    Returns:
        List of human-readable error strings.  Empty list = valid.

    Raises:
        ChunkValidationError: If raise_on_error=True and errors are found.
    """
    errors: list[str] = []

    if not chunks:
        return errors  # Empty chunk list is valid (empty document)

    # ── Rule 1: Non-empty text ─────────────────────────────────────────────────
    for chunk in chunks:
        if not chunk.chunk_text or not chunk.chunk_text.strip():
            errors.append(
                f"[empty-text] Chunk {chunk.chunk_index} has empty or whitespace-only text."
            )

    # ── Rule 2: Ordering (no gaps, starts at 0) ────────────────────────────────
    for expected_idx, chunk in enumerate(chunks):
        if chunk.chunk_index != expected_idx:
            errors.append(
                f"[ordering] Expected chunk_index={expected_idx}, "
                f"got chunk_index={chunk.chunk_index}."
            )

    # ── Rule 3: Offset monotonicity ────────────────────────────────────────────
    for i in range(1, len(chunks)):
        if chunks[i].start_offset < chunks[i - 1].start_offset:
            errors.append(
                f"[offset-monotonicity] Chunk {i} start_offset "
                f"({chunks[i].start_offset}) < chunk {i-1} start_offset "
                f"({chunks[i-1].start_offset})."
            )

    # ── Rule 4: Size limits ────────────────────────────────────────────────────
    for chunk in chunks:
        max_allowed = int(chunk.chunk_size * max_chunk_size_multiplier)
        if len(chunk.chunk_text) > max_allowed:
            errors.append(
                f"[size-limit] Chunk {chunk.chunk_index} has {len(chunk.chunk_text)} chars, "
                f"exceeding {max_allowed} (chunk_size={chunk.chunk_size} × "
                f"{max_chunk_size_multiplier})."
            )

    # ── Rule 5: Duplicate text prevention ─────────────────────────────────────
    seen_hashes: set[str] = set()
    for chunk in chunks:
        text_hash = _hash_text(chunk.chunk_text)
        if text_hash in seen_hashes:
            errors.append(
                f"[duplicate] Chunk {chunk.chunk_index} has identical text to a "
                f"previous chunk."
            )
        seen_hashes.add(text_hash)

    # ── Rule 6: Token sanity ───────────────────────────────────────────────────
    for chunk in chunks:
        if chunk.chunk_text.strip() and chunk.estimated_tokens <= 0:
            errors.append(
                f"[token-sanity] Chunk {chunk.chunk_index} has non-empty text but "
                f"estimated_tokens={chunk.estimated_tokens}."
            )

    if raise_on_error and errors:
        raise ChunkValidationError(errors)

    return errors


def assert_valid_chunks(
    chunks: list[ChunkData],
    max_chunk_size_multiplier: float = 2.0,
) -> None:
    """
    Assert that chunks are valid, raising ChunkValidationError if not.

    Convenience wrapper around :func:`validate_chunks` for use in services
    that want to fail fast.

    Args:
        chunks                   : ChunkData list to validate.
        max_chunk_size_multiplier: See :func:`validate_chunks`.

    Raises:
        ChunkValidationError: If any validation rule fails.
    """
    validate_chunks(
        chunks,
        max_chunk_size_multiplier=max_chunk_size_multiplier,
        raise_on_error=True,
    )


# ── Internal helpers ──────────────────────────────────────────────────────────

def _hash_text(text: str) -> str:
    """Return a short SHA-256 hex digest of the text for dedup detection."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]
