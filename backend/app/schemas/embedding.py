"""
Embedding Pydantic Schemas — Day 69 Part A2.

Internal and API response contracts for embedding metadata.

Security & Privacy Rules:
    - Raw vector values are NEVER returned in API schemas or log messages.
    - Provider credentials are NEVER returned.
    - user_id is internal; excluded from public schemas.
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class EmbeddingStatusResponse(BaseModel):
    """Operational metadata for a single chunk's embedding (excluding vector)."""

    id: str
    chunk_id: str
    parsed_document_id: str
    provider: str
    model_name: str
    model_version: str
    embedding_version: int
    dimension: int
    status: str
    failure_count: int = 0
    error_category: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class EmbeddingGenerationResult(BaseModel):
    """Returned after an embedding generation job finishes."""

    job_id: str
    document_id: str
    parsed_document_id: str
    model: str
    dimension: int
    embedding_version: int
    chunk_count: int
    ready: int
    failed: int
    skipped: int = 0
    duration_ms: float = 0.0
    message: str = "Embedding generation completed."


class DocumentEmbeddingStatusResponse(BaseModel):
    """Aggregate status counts for a document's embeddings."""

    document_id: str
    parsed_document_id: str
    model: str
    dimension: int
    ready: int
    pending: int
    processing: int
    failed: int
    archived: int
    total_active: int
