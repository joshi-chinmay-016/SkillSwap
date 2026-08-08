"""
SkillSwap Arena — Custom Exceptions Package.
"""
from app.exceptions.storage_exceptions import (
    StorageUnavailable,
    StorageWriteError,
    StorageReadError,
    StorageDeleteError,
    StorageValidationError,
)
from app.exceptions.embedding_exceptions import (
    EmbeddingError,
    EmbeddingProviderError,
    EmbeddingRateLimitError,
    EmbeddingTimeoutError,
    EmbeddingValidationError,
    EmbeddingConfigurationError,
    EmbeddingIdempotencyError,
)

__all__ = [
    # Storage
    "StorageUnavailable",
    "StorageWriteError",
    "StorageReadError",
    "StorageDeleteError",
    "StorageValidationError",
    # Embedding
    "EmbeddingError",
    "EmbeddingProviderError",
    "EmbeddingRateLimitError",
    "EmbeddingTimeoutError",
    "EmbeddingValidationError",
    "EmbeddingConfigurationError",
    "EmbeddingIdempotencyError",
]
