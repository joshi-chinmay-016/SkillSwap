"""
EmbeddingProvider — Abstract base class for embedding model providers (Day 69 Part A1).

This is the abstraction layer between the application and any concrete
embedding model or API. All embedding providers must implement this interface.

Design goals:
    - Provider-agnostic: EmbeddingService depends only on EmbeddingProvider.
    - Replaceable: swap Gemini → OpenAI → local model without changing service code.
    - Query-compatible: the same provider interface is reused for query embeddings
      in Day 71 (retriever), ensuring document and query vectors are always compatible.

Usage:
    provider: EmbeddingProvider = GeminiEmbeddingProvider()

    # Single embedding
    vector: list[float] = provider.generate_embedding("Hello world")

    # Batch embedding
    vectors: list[list[float]] = provider.generate_embeddings(["chunk1", "chunk2"])

    # Model metadata
    dim: int = provider.get_dimension()          # e.g. 768
    name: str = provider.get_model_name()        # e.g. "text-embedding-004"
    ver: str = provider.get_model_version()      # e.g. "v1"

Raises:
    EmbeddingConfigurationError  — when the provider cannot be initialised.
    EmbeddingProviderError       — for unexpected provider failures.
    EmbeddingRateLimitError      — HTTP 429 / quota exceeded.
    EmbeddingTimeoutError        — request exceeded configured timeout.
    EmbeddingValidationError     — provider returned malformed vector.
"""
from __future__ import annotations

from abc import ABC, abstractmethod


class EmbeddingProvider(ABC):
    """
    Abstract interface for an embedding model provider.

    Concrete implementations must not contain database logic, business rules,
    or retry mechanisms — those belong to EmbeddingService.
    """

    # ── Single embedding ───────────────────────────────────────────────────────

    @abstractmethod
    def generate_embedding(self, text: str) -> list[float]:
        """
        Generate a single embedding vector for the given text.

        Args:
            text: The input text to embed. Must not be empty.

        Returns:
            A list of floats with length == get_dimension().

        Raises:
            EmbeddingConfigurationError : Provider is not properly configured.
            EmbeddingProviderError      : Provider returned an unexpected error.
            EmbeddingRateLimitError     : Provider quota/rate limit reached.
            EmbeddingTimeoutError       : Request timed out.
            EmbeddingValidationError    : Returned vector is malformed.
        """
        ...

    # ── Batch embedding ────────────────────────────────────────────────────────

    @abstractmethod
    def generate_embeddings(self, texts: list[str]) -> list[list[float]]:
        """
        Generate embeddings for a batch of texts in a single provider call.

        Prefer this method over repeated calls to generate_embedding when
        processing multiple chunks — it is significantly more efficient.

        Args:
            texts: A non-empty list of input strings. All must be non-empty.

        Returns:
            A list of embedding vectors in the same order as `texts`.
            Each vector has length == get_dimension().

        Raises:
            EmbeddingConfigurationError : Provider is not properly configured.
            EmbeddingProviderError      : Provider returned an unexpected error.
            EmbeddingRateLimitError     : Provider quota/rate limit reached.
            EmbeddingTimeoutError       : Request timed out.
            EmbeddingValidationError    : One or more returned vectors are malformed.
        """
        ...

    # ── Model metadata ─────────────────────────────────────────────────────────

    @abstractmethod
    def get_dimension(self) -> int:
        """
        Return the output vector dimension for this model.

        This value must never be hardcoded in calling code — always retrieve
        it from the provider instance so that dimension changes on model swap
        are automatically reflected.

        Returns:
            Integer dimension (e.g. 768 for text-embedding-004).
        """
        ...

    @abstractmethod
    def get_model_name(self) -> str:
        """
        Return the canonical model name for this provider.

        Used for metadata tagging on every persisted embedding.

        Returns:
            Model name string (e.g. "text-embedding-004").
        """
        ...

    @abstractmethod
    def get_model_version(self) -> str:
        """
        Return the provider-level model version string.

        If the provider does not expose a version, return a stable
        application-managed version string (e.g. "v1").

        Returns:
            Version string (e.g. "v1", "001", "2024-01").
        """
        ...

    # ── Convenience helpers ────────────────────────────────────────────────────

    @property
    def provider_name(self) -> str:
        """
        Short identifier for this provider (e.g. 'gemini', 'openai').

        Defaults to the class name lowercased. Override for a cleaner label.
        """
        return self.__class__.__name__.lower().replace("embeddingprovider", "")

    def __repr__(self) -> str:
        return (
            f"<{self.__class__.__name__} "
            f"model={self.get_model_name()!r} "
            f"dim={self.get_dimension()}>"
        )
