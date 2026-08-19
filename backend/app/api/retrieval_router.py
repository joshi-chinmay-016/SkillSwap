"""
Retrieval Router — HTTP endpoints for vector retrieval (Day 71).

Prefix: /retrieval
Tags:   Retrieval Engine

Endpoints:
    POST /retrieval/search — Semantic retrieval across indexed document chunks

Security:
    - Requires authentication via get_current_user.
    - Ownership is enforced at the retriever layer.
    - Raw embeddings, FAISS IDs, and server paths are never exposed.
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.dependencies.current_user import get_current_user
from app.models.user import User
from app.retrieval import (
    InvalidRetrievalRequestError,
    QueryEmbeddingError,
    RetrievalError,
    RetrievalRequest,
    RetrievalService,
    RetrievalUnavailableError,
    VectorStoreSearchError,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/retrieval",
    tags=["Retrieval Engine"],
)


# ── Schemas ───────────────────────────────────────────────────────────────────

class RetrievalSearchApiRequest(BaseModel):
    query: str = Field(
        ...,
        description="Natural language search query.",
        json_schema_extra={"example": "What is dependency injection?"},
    )
    top_k: Optional[int] = Field(
        default=None,
        description="Maximum number of chunks to return (1 to max_top_k).",
        json_schema_extra={"example": 5},
    )
    similarity_threshold: Optional[float] = Field(
        default=None,
        description="Minimum similarity score threshold (0.0 to 1.0).",
        json_schema_extra={"example": 0.0},
    )
    document_id: Optional[str] = Field(
        default=None,
        description="Optional document UUID to restrict search scope.",
        json_schema_extra={"example": "2bb6bf0a-5e82-4102-80b4-924bc2163ae1"},
    )


class RetrievedChunkResponse(BaseModel):
    chunk_id: str
    document_id: str
    document_name: str
    content: str
    score: float
    rank: int


class RetrievalSearchApiResponse(BaseModel):
    results: list[RetrievedChunkResponse]
    total: int
    query_duration_ms: float
    embedding_ms: float
    faiss_ms: float
    db_ms: float


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post(
    "/search",
    response_model=RetrievalSearchApiResponse,
    summary="Semantic Retrieval Search",
    description="Retrieve relevant text chunks from user's indexed documents matching a query.",
)
def search_documents(
    body: RetrievalSearchApiRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        service = RetrievalService.create()
        req = RetrievalRequest(
            query=body.query,
            top_k=body.top_k if body.top_k is not None else 5,
            similarity_threshold=body.similarity_threshold if body.similarity_threshold is not None else 0.0,
            document_id=body.document_id,
        )
        response = service.retrieve(db, request=req, user_id=current_user.id)

        results_api = [
            RetrievedChunkResponse(
                chunk_id=item.chunk_id,
                document_id=item.document_id,
                document_name=item.document_name,
                content=item.content,
                score=item.score,
                rank=item.rank,
            )
            for item in response.results
        ]

        return RetrievalSearchApiResponse(
            results=results_api,
            total=response.total,
            query_duration_ms=response.query_duration_ms,
            embedding_ms=response.embedding_ms,
            faiss_ms=response.faiss_ms,
            db_ms=response.db_ms,
        )
    except InvalidRetrievalRequestError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc
    except RetrievalUnavailableError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Retrieval service is currently unavailable.",
        ) from exc
    except QueryEmbeddingError as exc:
        logger.error("Query embedding failed during retrieval: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to generate query embedding.",
        ) from exc
    except VectorStoreSearchError as exc:
        logger.error("Vector store search error: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Vector retrieval search failed.",
        ) from exc
    except RetrievalError as exc:
        logger.error("Retrieval error: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Retrieval operation failed.",
        ) from exc


class RetrievalMetricsApiResponse(BaseModel):
    total_documents: int
    total_chunks: int
    total_embeddings: int
    ready_embeddings: int
    failed_embeddings: int


@router.get(
    "/metrics",
    response_model=RetrievalMetricsApiResponse,
    summary="Retrieval Engine Metrics",
    description="Retrieve count metrics for user's indexed documents, chunks, and vector embeddings.",
)
def get_retrieval_metrics_endpoint(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        from app.retrieval.retrieval_repository import get_retrieval_metrics
        metrics = get_retrieval_metrics(db, user_id=current_user.id)
        return RetrievalMetricsApiResponse(
            total_documents=metrics.total_documents,
            total_chunks=metrics.total_chunks,
            total_embeddings=metrics.total_embeddings,
            ready_embeddings=metrics.ready_embeddings,
            failed_embeddings=metrics.failed_embeddings,
        )
    except Exception as exc:
        logger.error("Failed to retrieve retrieval metrics: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch retrieval metrics.",
        ) from exc

