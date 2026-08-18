"""
RAG Exceptions — Day 72 A1 + A2, Day 74 A1.

All RAG-layer errors inherit from RAGError.
User-facing messages are concise; internal details belong in logs.

Exception tree:
    RAGError (base)
    ├── ContextBuildError         — context construction failed unexpectedly
    ├── ContextValidationError    — a retrieved chunk failed validation
    ├── PromptBuildError          — prompt construction failed / prompt too large
    ├── GenerationError           — LLM provider failed (base for provider errors)
    │   ├── GenerationTimeoutError         — provider request timed out
    │   ├── GenerationProviderError        — provider-level API error
    │   └── InvalidGenerationResponseError — empty or malformed LLM response
    ├── SourceValidationFailure   — generated answer references invalid sources (Day 74)
    └── RAGUnavailableError       — underlying retrieval infrastructure unavailable

Error categories supported:
    NO_RELEVANT_KNOWLEDGE     — insufficient_context=True
    CONTEXT_BUILD_FAILURE     — ContextBuildError
    GENERATION_FAILURE        — GenerationError / GenerationProviderError / GenerationTimeoutError
    INVALID_GENERATION        — InvalidGenerationResponseError
    SOURCE_VALIDATION_FAILURE — SourceValidationFailure (Day 74)
    AUTHORIZATION_FAILURE     — enforced inside RetrievalService (not exposed as an exception)
    TIMEOUT                   — GenerationTimeoutError
"""
from __future__ import annotations


class RAGError(Exception):
    """Base class for all RAG-layer exceptions."""

    def __init__(self, message: str, *, cause: Exception | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.cause = cause

    def __str__(self) -> str:
        if self.cause:
            return (
                f"{self.message} "
                f"(caused by: {type(self.cause).__name__}: {self.cause})"
            )
        return self.message

    @property
    def is_recoverable(self) -> bool:
        """Whether callers may retry this operation."""
        return False


class RAGValidationError(RAGError):
    """
    Raised when input validation for a RAG request fails before downstream execution.

    Examples:
        - Query is empty or whitespace-only.
        - Query exceeds maximum character limit.
        - top_k is outside allowed range.
        - document_id is not a valid UUID format.
        - response_style is unsupported.
    """

    @property
    def is_recoverable(self) -> bool:
        return False


class ContextBuildError(RAGError):
    """
    Raised when the ContextBuilder fails to construct context unexpectedly.

    Examples:
        - An unhandled internal error during context formatting.
        - Budget configuration is invalid (e.g. max_chunks <= 0).

    This is NOT raised when chunks are simply empty or invalid — those cases
    are handled gracefully by the builder (skip + log).
    """

    @property
    def is_recoverable(self) -> bool:
        return False


class ContextValidationError(RAGError):
    """
    Raised when a retrieved chunk fails structural validation and the failure
    is severe enough to abort the build (e.g. entirely corrupt input list).

    In most cases individual bad chunks are skipped silently; this error is
    reserved for inputs that make it impossible to proceed at all.
    """

    @property
    def is_recoverable(self) -> bool:
        return False


class PromptBuildError(RAGError):
    """
    Raised when the PromptBuilder cannot construct a valid prompt.

    Examples:
        - Query is empty or whitespace-only.
        - Constructed prompt exceeds RAG_MAX_PROMPT_TOKENS.
        - Unsupported response style provided.
    """

    @property
    def is_recoverable(self) -> bool:
        return False  # Caller must fix the request


class GenerationError(RAGError):
    """
    Base class for LLM generation failures.

    Examples:
        - Provider returned an unexpected response shape.
        - Provider is unavailable.
    """

    @property
    def is_recoverable(self) -> bool:
        return True


class GenerationTimeoutError(GenerationError):
    """
    Raised when the LLM provider request exceeds the configured timeout.

    Examples:
        - Network stall during generation.
        - Provider takes too long to respond.
    """

    @property
    def is_recoverable(self) -> bool:
        return True


class GenerationProviderError(GenerationError):
    """
    Raised when the LLM provider returns an API-level error.

    Examples:
        - HTTP 429 rate limit from provider.
        - HTTP 503 provider unavailable.
        - Provider authentication failure.
    """

    @property
    def is_recoverable(self) -> bool:
        return True


class InvalidGenerationResponseError(GenerationError):
    """
    Raised when the LLM provider returns an empty or malformed response.

    Examples:
        - Empty answer string.
        - Missing required response fields.
        - Provider returned a refused/filtered response.
    """

    @property
    def is_recoverable(self) -> bool:
        return False  # Retrying with same prompt unlikely to help


class RAGUnavailableError(RAGError):
    """
    Raised when the underlying retrieval infrastructure is unavailable,
    making the entire RAG pipeline non-functional.

    Signals an infrastructure fault, not a user error.
    """

    @property
    def is_recoverable(self) -> bool:
        return False


class SourceValidationFailure(RAGError):
    """
    Raised when the AnswerValidator detects that the LLM-generated answer
    references source identifiers that are not present in the set of retrieved
    chunks — i.e., the model invented a source. (Day 74 A1)

    This exception is raised only when source fabrication cannot be silently
    corrected.  In most cases the AnswerValidator removes invalid sources and
    returns grounded=False rather than raising.

    Examples:
        - Answer references a chunk_id not in the retrieved set AND the
          remaining valid sources are empty while context was present.
    """

    @property
    def is_recoverable(self) -> bool:
        return False
