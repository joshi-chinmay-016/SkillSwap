"""
app/vector_store — FAISS Vector Storage module (Day 70).

Public exports:
    VectorStore         — abstract interface
    VectorStoreHealth   — health status dataclass
    FAISSVectorStore    — FAISS implementation
    All exception types
"""
from app.vector_store.base import VectorStore, VectorStoreHealth
from app.vector_store.faiss_store import FAISSVectorStore
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
    # Abstraction
    "VectorStore",
    "VectorStoreHealth",
    # Implementation
    "FAISSVectorStore",
    # Exceptions
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
