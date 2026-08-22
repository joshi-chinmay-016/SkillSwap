"""
RAG Router — HTTP endpoint for grounded generation (Day 72 A2).

Prefix: /rag
Tags:   RAG

Endpoints:
    POST /rag/query — Retrieval-augmented answer generation

Security:
    - Requires authentication via get_current_user.
    - Retriever authorization is enforced inside RAGService → RetrievalService.
    - Raw embeddings, FAISS IDs, server paths, and credentials are never exposed.
    - Stack traces, system prompts, and internal errors are never sent to clients.
    - Source identifiers are backend-controlled; LLM-generated citations are not trusted.

No chat history, streaming, multi-turn, or agent features are implemented.
"""
from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.dependencies.current_user import get_current_user
from app.models.user import User
from app.rag import (
    ContextBuildError,
    GenerationError,
    GenerationProviderError,
    GenerationTimeoutError,
    InvalidGenerationResponseError,
    PromptBuildError,
    RAGError,
    RAGService,
    RAGUnavailableError,
    RAGValidationError,
    SourceValidationFailure,
)
from app.retrieval import (
    InvalidRetrievalRequestError,
    QueryEmbeddingError,
    RetrievalError,
    RetrievalUnavailableError,
    VectorStoreSearchError,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/rag",
    tags=["RAG"],
)


# ── Request / Response Schemas ────────────────────────────────────────────────


class RAGQueryRequest(BaseModel):
    query: str = Field(
        ...,
        description="Natural language question to answer using indexed documents.",
        json_schema_extra={"example": "What is dependency injection?"},
        min_length=1,
    )
    top_k: Optional[int] = Field(
        default=None,
        description="Maximum number of chunks to retrieve (1 to max_top_k).",
        json_schema_extra={"example": 5},
        ge=1,
    )
    document_id: Optional[str] = Field(
        default=None,
        description="Optional document UUID to restrict retrieval scope.",
        json_schema_extra={"example": "2bb6bf0a-5e82-4102-80b4-924bc2163ae1"},
    )
    response_style: Optional[str] = Field(
        default=None,
        description="Response style: 'concise', 'detailed', or 'explanatory'.",
        json_schema_extra={"example": "detailed"},
    )


class RAGSourceResponse(BaseModel):
    chunk_id: str
    document_id: str
    document_name: str
    rank: int
    score: float


class RAGQueryResponse(BaseModel):
    answer: str
    sources: list[RAGSourceResponse]
    insufficient_context: bool
    context_chunk_count: int
    model: str
    grounded: bool = False  # Day 74 A1 — True when answer is validated and grounded


# ── Endpoints ─────────────────────────────────────────────────────────────────


@router.post(
    "/query",
    response_model=RAGQueryResponse,
    summary="RAG Query — Grounded Answer Generation",
    description=(
        "Retrieves relevant chunks from the user's indexed knowledge base "
        "and generates a grounded answer using the configured LLM. "
        "Requires authentication. Authorization is enforced at the retrieval layer."
    ),
)
def rag_query(
    body: RAGQueryRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> RAGQueryResponse:
    """
    Execute the full RAG pipeline: retrieve → context → prompt → generate.

    The answer is grounded in the user's own indexed documents.
    Source metadata is backend-controlled and traceable to retrieved chunks.
    """
    from app.core.rate_limiter import enforce_action_rate_limit
    enforce_action_rate_limit("rag_query", current_user.id, limit=20, window_seconds=60)

    try:
        service = RAGService.create()
        result = service.query(
            db,
            query=body.query,
            user_id=current_user.id,
            top_k=body.top_k,
            document_id=body.document_id,
            response_style=body.response_style,
        )

        sources_api = [
            RAGSourceResponse(
                chunk_id=src.chunk_id,
                document_id=src.document_id,
                document_name=src.document_name,
                rank=src.rank,
                score=src.score,
            )
            for src in result.sources
        ]

        return RAGQueryResponse(
            answer=result.answer,
            sources=sources_api,
            insufficient_context=result.insufficient_context,
            context_chunk_count=result.context_chunk_count,
            model=result.model,
            grounded=result.grounded,
        )

    # ── Client errors ─────────────────────────────────────────────────────────
    except RAGValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc

    except InvalidRetrievalRequestError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc

    except PromptBuildError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc

    # ── Infrastructure unavailable ────────────────────────────────────────────
    except (RAGUnavailableError, RetrievalUnavailableError) as exc:
        logger.error("RAG infrastructure unavailable: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="RAG service is currently unavailable.",
        ) from exc

    # ── Provider / generation errors ──────────────────────────────────────────
    except QueryEmbeddingError as exc:
        logger.error("RAG query embedding failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to generate query embedding.",
        ) from exc

    except GenerationTimeoutError as exc:
        logger.warning("RAG generation timed out: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Generation timed out. Please try again.",
        ) from exc

    except GenerationProviderError as exc:
        logger.error("RAG generation provider error: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Generation provider error. Please try again later.",
        ) from exc

    except InvalidGenerationResponseError as exc:
        logger.error("RAG received invalid generation response: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="The generation provider returned an invalid response.",
        ) from exc

    except SourceValidationFailure as exc:
        logger.error("RAG source validation failure: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Generated answer source validation failed.",
        ) from exc

    # ── Vector / context errors ────────────────────────────────────────────────
    except VectorStoreSearchError as exc:
        logger.error("RAG vector store search error: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Vector retrieval search failed.",
        ) from exc

    except ContextBuildError as exc:
        logger.error("RAG context build error: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Context construction failed.",
        ) from exc

    # ── Catch-all ─────────────────────────────────────────────────────────────
    except (RAGError, RetrievalError) as exc:
        logger.error("RAG pipeline error: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="RAG pipeline failed.",
        ) from exc

    except Exception as exc:
        logger.exception("Unexpected error in RAG query endpoint: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred.",
        ) from exc
