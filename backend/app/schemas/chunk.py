"""
Chunk Pydantic Schemas — Day 68 Part A2.

Internal API contract for chunk data used by services and future endpoints.

Security:
    - chunk_text is included in detail responses but excluded from list summaries.
    - user_id is never returned in public-facing schemas.
"""
from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field

from app.models.chunk import ChunkStatus


# ──────────────────────────────────────────────────────────────────────────────
# Internal schemas (service-to-service)
# ──────────────────────────────────────────────────────────────────────────────

class ChunkSummary(BaseModel):
    """Compact representation without chunk_text — used in list responses."""

    id: str
    parsed_document_id: str
    chunk_index: int
    estimated_tokens: int
    chunk_size: int
    overlap_size: int
    start_offset: int
    end_offset: int
    page_start: Optional[int] = None
    page_end: Optional[int] = None
    section: Optional[str] = None
    strategy: str
    strategy_version: str
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ChunkDetail(BaseModel):
    """Full chunk representation including chunk_text."""

    id: str
    parsed_document_id: str
    chunk_index: int
    chunk_text: str
    estimated_tokens: int
    chunk_size: int
    overlap_size: int
    start_offset: int
    end_offset: int
    page_start: Optional[int] = None
    page_end: Optional[int] = None
    section: Optional[str] = None
    strategy: str
    strategy_version: str
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ──────────────────────────────────────────────────────────────────────────────
# Chunk Metadata (aggregate)
# ──────────────────────────────────────────────────────────────────────────────

class ChunkMetadata(BaseModel):
    """Aggregate metadata for a parsed document's chunk set."""

    parsed_document_id: str
    total_chunks: int
    strategy: str
    strategy_version: str
    chunk_size: int
    overlap_size: int
    total_chars: int
    total_estimated_tokens: int
    average_chunk_size: float
    average_chunk_tokens: float
    status_counts: dict[str, int] = Field(default_factory=dict)


# ──────────────────────────────────────────────────────────────────────────────
# List response
# ──────────────────────────────────────────────────────────────────────────────

class ChunkListResponse(BaseModel):
    """Paginated list of chunk details."""

    parsed_document_id: str
    chunks: List[ChunkDetail]
    total: int
    page: int
    page_size: int
    has_next: bool
    has_previous: bool


# ──────────────────────────────────────────────────────────────────────────────
# Generation response
# ──────────────────────────────────────────────────────────────────────────────

class ChunkGenerationResult(BaseModel):
    """Returned by ChunkService after generating and persisting chunks."""

    parsed_document_id: str
    chunk_count: int
    strategy: str
    strategy_version: str
    chunk_size: int
    overlap_size: int
    status: str = "READY"
    message: str = "Chunks generated successfully."
