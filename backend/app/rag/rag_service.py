"""
RAGService — Day 72 Part A2.

Orchestrates the complete retrieval-augmented generation pipeline:

    User Query
        │
        ▼
    RetrievalService (Day 71)       — vector search + auth + filtering
        │
        ▼
    ContextBuilder (Day 72 A1)      — validation + dedup + budget + format
        │
        ▼
    PromptBuilder (Day 72 A2)       — grounded prompt construction
        │
        ▼
    LLMService (existing)           — Gemini generation
        │
        ▼
    GenerationResult                — answer + backend-controlled sources

Design:
    - Uses RetrievalService.create() — does NOT access FAISS directly.
    - Uses DefaultContextBuilder.from_settings() — does NOT duplicate context logic.
    - Uses GroundedPromptBuilder.from_settings() — does NOT duplicate prompt logic.
    - Uses LLMService (existing) — does NOT duplicate the LLM provider.
    - All dependencies are injectable for testing (mock-friendly constructor).

Security:
    - Authorization occurs inside RetrievalService (Day 71).
    - RAGService receives only authorized, lifecycle-filtered chunks.
    - ContextBuilder receives only pre-authorized chunks.
    - PromptBuilder builds application-level instructions only.
    - Source metadata is backend-controlled; never trusted from LLM output.
    - No raw context, queries, or answers are logged (private user data).
    - No API keys, credentials, or stack traces reach the API response.

Observability (logged at INFO):
    - retrieval_ms
    - context_build_ms
    - prompt_build_ms
    - generation_ms
    - total_ms
    - retrieved_chunk_count
    - context_chunk_count
    - answer_length
    - insufficient_context

No chat history, streaming, agents, or tool calling is implemented.
"""
from __future__ import annotations

import logging
import time
import uuid
from typing import Optional

from sqlalchemy.orm import Session

from app.core.config import settings
from app.rag.context_builder import ContextBuilder, DefaultContextBuilder
from app.rag.context_exceptions import (
    ContextBuildError,
    GenerationError,
    GenerationProviderError,
    GenerationTimeoutError,
    InvalidGenerationResponseError,
    PromptBuildError,
    RAGError,
    RAGUnavailableError,
)
from app.rag.context_models import ContextRequest
from app.rag.prompt_builder import GroundedPromptBuilder, PromptBuilder
from app.rag.prompt_models import GenerationResult, PromptRequest
from app.retrieval.retrieval_exceptions import (
    RetrievalError,
    RetrievalUnavailableError,
)
from app.retrieval.retrieval_models import RetrievalRequest

logger = logging.getLogger(__name__)


class RAGService:
    """
    Orchestrates the full RAG pipeline from user query to grounded answer.

    Usage::

        service = RAGService.create()
        result = service.query(
            db,
            query="What is dependency injection?",
            user_id=current_user.id,
        )
        print(result.answer)
        for source in result.sources:
            print(source.document_name, source.chunk_id)
    """

    def __init__(
        self,
        retrieval_service,          # RetrievalService — typed loosely to avoid circular import
        context_builder: ContextBuilder,
        prompt_builder: PromptBuilder,
        llm_service,                # LLMService — typed loosely to avoid circular import
    ) -> None:
        """
        Args:
            retrieval_service : Initialized RetrievalService (Day 71).
            context_builder   : Initialized ContextBuilder (Day 72 A1).
            prompt_builder    : Initialized PromptBuilder (Day 72 A2).
            llm_service       : Initialized LLMService (existing).
        """
        self._retrieval_service = retrieval_service
        self._context_builder = context_builder
        self._prompt_builder = prompt_builder
        self._llm_service = llm_service

    # ── Factory ───────────────────────────────────────────────────────────────

    @classmethod
    def create(cls) -> "RAGService":
        """
        Construct a RAGService from application settings.

        Initializes all dependencies using their own factory methods.
        No configuration is duplicated.

        Returns:
            Ready-to-use RAGService.

        Raises:
            RAGUnavailableError: Vector store cannot be initialized.
        """
        from app.ai.services.llm_service import LLMService
        from app.retrieval.retrieval_service import RetrievalService
        from app.retrieval.retrieval_exceptions import RetrievalUnavailableError

        try:
            retrieval_service = RetrievalService.create()
        except RetrievalUnavailableError as exc:
            raise RAGUnavailableError(
                "FAISS vector store could not be initialized for RAG pipeline.",
                cause=exc,
            ) from exc

        context_builder = DefaultContextBuilder.from_settings()
        prompt_builder = GroundedPromptBuilder.from_settings()
        llm_service = LLMService()

        return cls(
            retrieval_service=retrieval_service,
            context_builder=context_builder,
            prompt_builder=prompt_builder,
            llm_service=llm_service,
        )

    # ── Public interface ──────────────────────────────────────────────────────

    def query(
        self,
        db: Session,
        *,
        query: str,
        user_id: int,
        top_k: Optional[int] = None,
        document_id: Optional[str] = None,
        response_style: Optional[str] = None,
    ) -> GenerationResult:
        """
        Execute the full RAG pipeline and return a grounded generation result.

        Args:
            db            : Active SQLAlchemy session (read-only, used by Retriever).
            query         : Natural-language user question. Must be non-empty.
            user_id       : Authenticated user ID for ownership enforcement.
            top_k         : Optional override for retrieval top-k count.
            document_id   : Optional document UUID to scope retrieval.
            response_style: Optional generation style ("concise"|"detailed"|"explanatory").

        Returns:
            GenerationResult with answer, backend-controlled sources, and metadata.

        Raises:
            PromptBuildError     : Invalid query or prompt too large.
            ContextBuildError    : Context construction failed unexpectedly.
            GenerationError      : LLM provider failed.
            RetrievalError       : Retrieval pipeline failed.
            RAGUnavailableError  : Infrastructure unavailable.
        """
        request_id = str(uuid.uuid4())[:8]
        t_total_start = time.perf_counter()

        logger.info(
            "RAGService.query — request_id=%s user_id=%d "
            "top_k=%s document_scoped=%s style=%s",
            request_id, user_id, top_k, document_id is not None, response_style,
        )

        # ── Step 1: Retrieval ─────────────────────────────────────────────────
        t_retrieval_start = time.perf_counter()
        retrieval_req = RetrievalRequest(
            query=query,
            top_k=top_k if top_k is not None else getattr(settings, "RETRIEVAL_DEFAULT_TOP_K", 5),
            document_id=document_id,
        )
        retrieval_response = self._retrieval_service.retrieve(
            db,
            request=retrieval_req,
            user_id=user_id,
        )
        retrieval_ms = (time.perf_counter() - t_retrieval_start) * 1000

        retrieved_chunks = retrieval_response.results
        retrieved_count = len(retrieved_chunks)

        # ── Step 2: Context building ──────────────────────────────────────────
        t_context_start = time.perf_counter()
        context_req = ContextRequest(retrieved_chunks=retrieved_chunks)
        context_result = self._context_builder.build(context_req)
        context_build_ms = (time.perf_counter() - t_context_start) * 1000

        insufficient_context = context_result.chunk_count == 0

        # ── Step 3: Prompt building ───────────────────────────────────────────
        t_prompt_start = time.perf_counter()
        prompt_req = PromptRequest(
            query=query,
            context_result=context_result,
            response_style=response_style,
        )
        prompt_result = self._prompt_builder.build(prompt_req)
        prompt_build_ms = (time.perf_counter() - t_prompt_start) * 1000

        # ── Step 4: Generation ────────────────────────────────────────────────
        t_generation_start = time.perf_counter()
        answer = self._call_llm(
            request_id=request_id,
            system_instruction=prompt_result.system_instruction,
            user_message=prompt_result.user_message,
        )
        generation_ms = (time.perf_counter() - t_generation_start) * 1000

        total_ms = (time.perf_counter() - t_total_start) * 1000

        logger.info(
            "RAGService.query — request_id=%s "
            "retrieved_chunks=%d context_chunks=%d answer_length=%d "
            "insufficient_context=%s truncated=%s "
            "retrieval_ms=%.1f context_ms=%.1f prompt_ms=%.1f "
            "generation_ms=%.1f total_ms=%.1f",
            request_id,
            retrieved_count,
            context_result.chunk_count,
            len(answer),
            insufficient_context,
            context_result.truncated,
            retrieval_ms,
            context_build_ms,
            prompt_build_ms,
            generation_ms,
            total_ms,
        )

        return GenerationResult(
            answer=answer,
            sources=prompt_result.sources,  # backend-controlled, from ContextBuilder
            model=getattr(settings, "GEMINI_MODEL", ""),
            insufficient_context=insufficient_context,
            context_chunk_count=context_result.chunk_count,
        )

    # ── Private helpers ───────────────────────────────────────────────────────

    def _call_llm(
        self,
        *,
        request_id: str,
        system_instruction: str,
        user_message: str,
    ) -> str:
        """
        Call the LLM provider via LLMService and return the answer text.

        Args:
            request_id        : Short request identifier for logging.
            system_instruction: Grounding rules (application-controlled).
            user_message      : Query + context block (user-turn).

        Returns:
            Generated answer string.  Empty string if the provider returns nothing.

        Raises:
            GenerationTimeoutError   : Provider request timed out.
            GenerationProviderError  : Provider returned an API-level error.
            InvalidGenerationResponseError: Provider returned empty/malformed response.
            GenerationError          : Any other generation failure.
        """
        temperature: float = getattr(settings, "RAG_TEMPERATURE", 0.2)

        try:
            raw_answer: str = self._llm_service.generate(
                prompt=user_message,
                system_prompt=system_instruction,
                temperature=temperature,
            )
        except TimeoutError as exc:
            raise GenerationTimeoutError(
                "LLM generation timed out.",
                cause=exc,
            ) from exc
        except RuntimeError as exc:
            # GeminiProvider raises RuntimeError for HTTP errors and connection errors
            err_msg = str(exc).lower()
            if "429" in err_msg or "rate" in err_msg or "quota" in err_msg:
                raise GenerationProviderError(
                    "LLM provider rate limit or quota exceeded.",
                    cause=exc,
                ) from exc
            if "503" in err_msg or "unavailable" in err_msg or "connect" in err_msg:
                raise GenerationProviderError(
                    "LLM provider is unavailable.",
                    cause=exc,
                ) from exc
            raise GenerationError(
                "LLM generation failed.",
                cause=exc,
            ) from exc
        except Exception as exc:
            raise GenerationError(
                "Unexpected error during LLM generation.",
                cause=exc,
            ) from exc

        # Validate response
        if not raw_answer or not raw_answer.strip():
            logger.warning(
                "RAGService — LLM returned empty response. request_id=%s",
                request_id,
            )
            raise InvalidGenerationResponseError(
                "LLM provider returned an empty response."
            )

        return raw_answer.strip()
