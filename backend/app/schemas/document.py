"""
Document Pydantic Schemas — Day 66 Part A1.

API contract for document upload, listing, detail, rename, and delete endpoints.

Security note:
    ``checksum`` and ``storage_path`` are intentionally EXCLUDED from all
    response schemas — they must never be exposed to the frontend.
"""
from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator

from app.models.document import DocumentStatus


# ──────────────────────────────────────────────────────────────────────────────
# Request schemas
# ──────────────────────────────────────────────────────────────────────────────

class DocumentRenameRequest(BaseModel):
    """
    PATCH /documents/{id} — update the display name only.

    The stored filename is never modified.
    """

    display_name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="New human-readable display name for the document.",
        examples=["Algorithms Notes — Revised"],
    )

    @field_validator("display_name", mode="before")
    @classmethod
    def strip_whitespace(cls, v: str) -> str:
        return v.strip() if isinstance(v, str) else v


class DocumentFilterParams(BaseModel):
    """Query parameters for GET /documents."""

    status: Optional[DocumentStatus] = Field(
        default=None,
        description="Filter by document status.",
    )
    page: int = Field(default=1, ge=1, description="Page number (1-indexed).")
    page_size: int = Field(default=20, ge=1, le=100, description="Records per page.")
    sort: str = Field(
        default="newest",
        description="Sort order: 'newest', 'oldest', or 'name'.",
    )

    @field_validator("sort", mode="before")
    @classmethod
    def validate_sort(cls, v: str) -> str:
        allowed = {"newest", "oldest", "name"}
        v = v.lower().strip() if isinstance(v, str) else v
        if v not in allowed:
            raise ValueError(f"sort must be one of: {', '.join(sorted(allowed))}")
        return v


# ──────────────────────────────────────────────────────────────────────────────
# Response schemas
# ──────────────────────────────────────────────────────────────────────────────

class DocumentUploadResponse(BaseModel):
    """
    Returned immediately after a successful upload (POST /documents/upload).

    Intentionally minimal — the full record is available via GET /documents/{id}.
    """

    id: str
    display_name: str
    original_filename: str
    file_extension: str
    mime_type: str
    file_size: int
    status: str
    uploaded_at: datetime

    model_config = {"from_attributes": True}


class DocumentDetailResponse(BaseModel):
    """
    Full document metadata returned by GET /documents/{id} and PATCH /documents/{id}.

    Deliberately excludes:
        - checksum  (security — internal use only)
        - storage_path  (security — internal use only)
        - deleted_at  (internal soft-delete marker)
    """

    id: str
    user_id: int
    original_filename: str
    stored_filename: str
    display_name: str
    file_extension: str
    mime_type: str
    file_size: int
    status: str
    uploaded_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class DocumentListItem(BaseModel):
    """
    Compact representation used in paginated list responses.
    """

    id: str
    display_name: str
    original_filename: str
    file_extension: str
    file_size: int
    status: str
    uploaded_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class DocumentListResponse(BaseModel):
    """
    Paginated list of documents (GET /documents).
    """

    documents: List[DocumentListItem]
    total: int
    page: int
    page_size: int
    has_next: bool
    has_previous: bool


class DocumentDeleteResponse(BaseModel):
    """
    Confirmation returned after a successful soft-delete (DELETE /documents/{id}).
    """

    id: str
    status: str
    message: str


class DocumentMetricsResponse(BaseModel):
    """
    Upload / storage metrics exposed to administrators.
    Returned by GET /documents/metrics.
    """

    uploads_total: int
    uploads_failed: int
    downloads_total: int
    downloads_failed: int
    deletes_total: int
    total_bytes_uploaded: int
    average_upload_size_bytes: Optional[float] = None
    average_upload_latency_ms: Optional[float] = None
    duplicate_rate: Optional[float] = None


class StorageHealthResponse(BaseModel):
    """
    Storage health status for the /documents/health endpoint.
    """

    healthy: bool
    provider: str
    directory_exists: bool
    directory_readable: bool
    directory_writable: bool
    disk_free_bytes: Optional[int] = None
    disk_usage_percent: Optional[float] = None
    errors: List[str] = []


# ──────────────────────────────────────────────────────────────────────────────
# Parsed document (Day 67)
# ──────────────────────────────────────────────────────────────────────────────

class ParsedDocumentResponse(BaseModel):
    """
    Extracted text from a document (GET /documents/{id}/parsed).

    ``text_content`` may be empty if parsing is still in progress or failed.
    """

    document_id: str
    status: str
    text_content: str = ""
    char_count: int = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}

