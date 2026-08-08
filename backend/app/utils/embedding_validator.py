"""
embedding_validator — Vector validation for generated embeddings (Day 69 Part A1).

Pure Python module — no database access, no provider SDK dependency.

Validation checks (run in this order):
    1. Vector exists (not None)
    2. Vector is non-empty (len > 0)
    3. All values are numeric (int or float)
    4. No NaN values
    5. No Infinity values
    6. Dimension matches expected value

Security:
    - Vector values are never logged.
    - Only operational metadata (chunk_id, dimension) appears in log messages.
"""
from __future__ import annotations

import math

from app.exceptions.embedding_exceptions import EmbeddingValidationError


def validate_vector(
    vector: list[float] | None,
    expected_dimension: int,
    *,
    chunk_id: str | None = None,
) -> None:
    """
    Validate a single embedding vector against the expected dimension.

    Args:
        vector            : The vector to validate (list of floats).
        expected_dimension: The exact number of elements the vector must contain.
        chunk_id          : Optional chunk identifier for better error messages.

    Raises:
        EmbeddingValidationError: If any validation check fails.
    """
    label = f"chunk_id={chunk_id!r}" if chunk_id else "vector"

    # 1. Exists
    if vector is None:
        raise EmbeddingValidationError(
            f"[{label}] Vector is None — provider returned no embedding.",
            chunk_id=chunk_id,
            expected_dimension=expected_dimension,
            actual_dimension=None,
        )

    # 2. Non-empty
    if len(vector) == 0:
        raise EmbeddingValidationError(
            f"[{label}] Vector is empty (length=0).",
            chunk_id=chunk_id,
            expected_dimension=expected_dimension,
            actual_dimension=0,
        )

    # 3. Numeric
    for i, val in enumerate(vector):
        if not isinstance(val, (int, float)):
            raise EmbeddingValidationError(
                f"[{label}] Non-numeric value at index {i}: "
                f"type={type(val).__name__!r}.",
                chunk_id=chunk_id,
                expected_dimension=expected_dimension,
                actual_dimension=len(vector),
            )

    # 4. No NaN
    nan_indices = [i for i, v in enumerate(vector) if math.isnan(v)]
    if nan_indices:
        raise EmbeddingValidationError(
            f"[{label}] Vector contains NaN at indices {nan_indices[:5]}"
            f"{'...' if len(nan_indices) > 5 else ''}.",
            chunk_id=chunk_id,
            expected_dimension=expected_dimension,
            actual_dimension=len(vector),
        )

    # 5. No Infinity
    inf_indices = [i for i, v in enumerate(vector) if math.isinf(v)]
    if inf_indices:
        raise EmbeddingValidationError(
            f"[{label}] Vector contains Infinity at indices {inf_indices[:5]}"
            f"{'...' if len(inf_indices) > 5 else ''}.",
            chunk_id=chunk_id,
            expected_dimension=expected_dimension,
            actual_dimension=len(vector),
        )

    # 6. Dimension check
    actual = len(vector)
    if actual != expected_dimension:
        raise EmbeddingValidationError(
            f"[{label}] Dimension mismatch: expected={expected_dimension}, "
            f"actual={actual}. Check EMBEDDING_MODEL configuration.",
            chunk_id=chunk_id,
            expected_dimension=expected_dimension,
            actual_dimension=actual,
        )


def validate_vectors(
    vectors: list[list[float] | None],
    expected_dimension: int,
    *,
    chunk_ids: list[str] | None = None,
) -> list[str]:
    """
    Validate a batch of vectors.

    Args:
        vectors           : List of vectors (may contain None on provider failure).
        expected_dimension: Expected dimension for every vector.
        chunk_ids         : Optional list of chunk IDs (same length as vectors).

    Returns:
        List of validation error messages. Empty list means all vectors are valid.
    """
    errors: list[str] = []
    ids = chunk_ids or [None] * len(vectors)  # type: ignore[list-item]

    for i, (vector, chunk_id) in enumerate(zip(vectors, ids)):
        try:
            validate_vector(vector, expected_dimension, chunk_id=chunk_id)
        except EmbeddingValidationError as exc:
            errors.append(f"[index={i}] {exc.message}")

    return errors


def is_valid_vector(
    vector: list[float] | None,
    expected_dimension: int,
) -> bool:
    """
    Return True if vector passes all validation checks, False otherwise.

    Convenience wrapper for use in conditional logic without exception handling.
    """
    try:
        validate_vector(vector, expected_dimension)
        return True
    except EmbeddingValidationError:
        return False
