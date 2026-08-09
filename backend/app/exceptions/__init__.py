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
from app.vector_store.exceptions import (
    VectorStoreError,
    VectorStoreInitializationError,
    FAISSIndexError,
    VectorDimensionMismatchError,
    VectorStorePersistenceError,
    VectorMappingError,
    VectorIndexingError,
    VectorRebuildError,
    VectorConsistencyError,
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
    # Vector Store
    "VectorStoreError",
    "VectorStoreInitializationError",
    "FAISSIndexError",
    "VectorDimensionMismatchError",
    "VectorStorePersistenceError",
    "VectorMappingError",
    "VectorIndexingError",
    "VectorRebuildError",
    "VectorConsistencyError",
]
