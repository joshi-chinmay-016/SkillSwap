"""
Embeddings package — Day 69 Part A1.

Provides the EmbeddingProvider interface and EmbeddingResult data class.
Concrete provider implementations live in embeddings/providers/.
"""
from app.embeddings.embedding_provider import EmbeddingProvider
from app.embeddings.embedding_result import EmbeddingResult

__all__ = [
    "EmbeddingProvider",
    "EmbeddingResult",
]
