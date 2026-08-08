"""
Embedding providers sub-package — Day 69 Part A1.

Contains concrete implementations of EmbeddingProvider.

Currently supported:
    - GeminiEmbeddingProvider: Google Gemini text-embedding-004

Future:
    - OpenAIEmbeddingProvider
    - LocalEmbeddingProvider (sentence-transformers)
"""
from app.embeddings.providers.gemini_embedding_provider import GeminiEmbeddingProvider

__all__ = ["GeminiEmbeddingProvider"]
