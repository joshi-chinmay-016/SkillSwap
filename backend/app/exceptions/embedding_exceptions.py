"""
Embedding Exceptions — Day 69 Part A1.

Custom exception hierarchy for the Embedding Generation Engine.
Never expose raw provider SDK exceptions outside this layer.

Exception tree:
    EmbeddingError (base)
    ├── EmbeddingProviderError       — generic provider failure
    ├── EmbeddingRateLimitError      — HTTP 429 / quota exceeded
    ├── EmbeddingTimeoutError        — request timed out
    ├── EmbeddingValidationError     — vector failed validation checks
    ├── EmbeddingConfigurationError  — missing/invalid configuration
    └── EmbeddingIdempotencyError    — embedding already exists (skip signal)
"""


class EmbeddingError(Exception):
    """Base class for all embedding-layer exceptions."""

    def __init__(self, message: str, *, cause: Exception | None = None) -> None:
        super().__init__(message)
        self.cause = cause
        self.message = message

    def __str__(self) -> str:
        if self.cause:
            return f"{self.message} (caused by: {self.cause})"
        return self.message

    @property
    def is_recoverable(self) -> bool:
        """Whether this error is safe to retry."""
        return False


class EmbeddingProviderError(EmbeddingError):
    """
    Raised when the embedding provider returns an unexpected error.

    Examples:
        - HTTP 500 from provider API.
        - Unexpected response format.
        - Provider-level failure not otherwise classified.
    """

    @property
    def is_recoverable(self) -> bool:
        return True


class EmbeddingRateLimitError(EmbeddingError):
    """
    Raised when the provider signals rate limit or quota exhaustion.

    Examples:
        - HTTP 429 Too Many Requests.
        - Quota exceeded message in response.
        - RPM (requests-per-minute) limit hit.
    """

    @property
    def is_recoverable(self) -> bool:
        return True


class EmbeddingTimeoutError(EmbeddingError):
    """
    Raised when a provider call exceeds the configured timeout.

    Examples:
        - urllib timeout.
        - SDK request timeout.
        - Network stall.
    """

    @property
    def is_recoverable(self) -> bool:
        return True


class EmbeddingValidationError(EmbeddingError):
    """
    Raised when a generated vector fails validation.

    Examples:
        - Wrong dimension (e.g. 512 instead of 768).
        - Contains NaN or Infinity.
        - Empty vector returned.
        - Non-numeric values.

    This is NOT recoverable — the provider returned bad data.
    Retrying with the same input is unlikely to help unless the
    provider has a bug.
    """

    def __init__(
        self,
        message: str,
        *,
        chunk_id: str | None = None,
        expected_dimension: int | None = None,
        actual_dimension: int | None = None,
        cause: Exception | None = None,
    ) -> None:
        super().__init__(message, cause=cause)
        self.chunk_id = chunk_id
        self.expected_dimension = expected_dimension
        self.actual_dimension = actual_dimension

    @property
    def is_recoverable(self) -> bool:
        return False


class EmbeddingConfigurationError(EmbeddingError):
    """
    Raised when the embedding system is misconfigured.

    Examples:
        - EMBEDDING_API_KEY not set.
        - Unsupported EMBEDDING_PROVIDER value.
        - EMBEDDING_MODEL refers to a non-existent model.

    This is NOT recoverable — the configuration must be fixed first.
    """

    @property
    def is_recoverable(self) -> bool:
        return False


class EmbeddingIdempotencyError(EmbeddingError):
    """
    Raised (as a control-flow signal) when a valid embedding already
    exists for the same chunk / model / version combination.

    This is intentionally non-fatal and means the caller should skip
    this chunk rather than treating it as a hard failure.
    """

    def __init__(
        self,
        message: str,
        *,
        chunk_id: str | None = None,
        embedding_id: str | None = None,
        cause: Exception | None = None,
    ) -> None:
        super().__init__(message, cause=cause)
        self.chunk_id = chunk_id
        self.embedding_id = embedding_id

    @property
    def is_recoverable(self) -> bool:
        return False
