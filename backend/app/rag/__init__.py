"""
RAG Package — Day 72 A1 + A2, Day 74 A1.

Public surface for the RAG layer.

A1 — Context Builder:
    ContextBuilder          abstract base
    DefaultContextBuilder   production implementation
    ContextRequest          input dataclass
    ContextResult           output dataclass
    ContextSource           per-source traceability record

A2 — Prompt Builder + Generation:
    PromptBuilder           abstract base
    GroundedPromptBuilder   production implementation
    PromptRequest           prompt input dataclass
    PromptResult            structured prompt for LLMService
    GenerationResult        final grounded answer

Day 74 A1 — Answer Validator:
    AnswerValidator         validates LLM output before returning
    AnswerValidationResult  structured validation result

Exceptions:
    RAGError                base
    ContextBuildError
    ContextValidationError
    PromptBuildError
    GenerationError
    GenerationTimeoutError
    GenerationProviderError
    InvalidGenerationResponseError
    SourceValidationFailure  (Day 74 A1)
    RAGUnavailableError

Orchestration:
    RAGService              end-to-end pipeline orchestrator
"""

from app.rag.answer_validator import AnswerValidationResult, AnswerValidator
from app.rag.context_builder import ContextBuilder, DefaultContextBuilder
from app.rag.context_exceptions import (
    ContextBuildError,
    ContextValidationError,
    GenerationError,
    GenerationProviderError,
    GenerationTimeoutError,
    InvalidGenerationResponseError,
    PromptBuildError,
    RAGError,
    RAGUnavailableError,
    RAGValidationError,
    SourceValidationFailure,
)
from app.rag.context_models import ContextRequest, ContextResult, ContextSource
from app.rag.prompt_builder import GroundedPromptBuilder, PromptBuilder
from app.rag.prompt_models import GenerationResult, PromptRequest, PromptResult
from app.rag.rag_service import RAGService

__all__ = [
    # Context builder
    "ContextBuilder",
    "DefaultContextBuilder",
    "ContextRequest",
    "ContextResult",
    "ContextSource",
    # Prompt builder
    "PromptBuilder",
    "GroundedPromptBuilder",
    "PromptRequest",
    "PromptResult",
    # Generation
    "GenerationResult",
    # Answer Validator (Day 74 A1)
    "AnswerValidator",
    "AnswerValidationResult",
    # RAG orchestration
    "RAGService",
    # Exceptions
    "RAGError",
    "RAGValidationError",
    "ContextBuildError",
    "ContextValidationError",
    "PromptBuildError",
    "GenerationError",
    "GenerationTimeoutError",
    "GenerationProviderError",
    "InvalidGenerationResponseError",
    "SourceValidationFailure",
    "RAGUnavailableError",
]
