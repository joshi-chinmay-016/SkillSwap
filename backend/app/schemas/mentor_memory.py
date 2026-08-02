"""
MentorMemory Pydantic schemas.

Validates API input/output for long-term memory CRUD and filtering.
"""
from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, Field, field_validator

from app.models.mentor_memory import MemoryCategory, MemoryImportance, MemoryStatus, MemorySource


# ──────────────────────────────────────────────────────────────────────────────
# Request schemas
# ──────────────────────────────────────────────────────────────────────────────

class MentorMemoryCreate(BaseModel):
    """Payload to create a new long-term memory."""

    category: MemoryCategory = Field(
        default=MemoryCategory.GENERAL,
        description="Memory category — determines retrieval context.",
    )
    title: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Short descriptive title for the memory.",
    )
    content: str = Field(
        ...,
        min_length=1,
        description="Full text of the memory fact.",
    )
    importance: MemoryImportance = Field(
        default=MemoryImportance.MEDIUM,
        description="Priority level — affects retrieval ranking.",
    )
    source: MemorySource = Field(
        default=MemorySource.CONVERSATION,
        description="Where this memory originated.",
    )
    is_pinned: bool = Field(
        default=False,
        description="Pinned memories always get retrieval priority.",
    )

    @field_validator("title", "content", mode="before")
    @classmethod
    def strip_whitespace(cls, v: str) -> str:
        return v.strip() if v else v


class MentorMemoryUpdate(BaseModel):
    """Partial-update payload — all fields optional."""

    category: Optional[MemoryCategory] = None
    title: Optional[str] = Field(default=None, min_length=1, max_length=255)
    content: Optional[str] = Field(default=None, min_length=1)
    importance: Optional[MemoryImportance] = None
    source: Optional[MemorySource] = None
    is_pinned: Optional[bool] = None

    @field_validator("title", "content", mode="before")
    @classmethod
    def strip_whitespace(cls, v: Optional[str]) -> Optional[str]:
        return v.strip() if v else v


# ──────────────────────────────────────────────────────────────────────────────
# Response schemas
# ──────────────────────────────────────────────────────────────────────────────

class MentorMemoryResponse(BaseModel):
    """Single memory record returned to the API caller."""

    id: int
    user_id: int
    category: str
    title: str
    content: str
    importance: str
    source: str
    status: str
    is_pinned: bool
    created_at: datetime
    updated_at: datetime
    last_used_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class MentorMemoryListResponse(BaseModel):
    """Paginated list of memories."""

    memories: List[MentorMemoryResponse]
    total: int
    page: int
    page_size: int


class MentorMemoryStatsResponse(BaseModel):
    """Aggregated memory dashboard metrics for the current user."""

    total_memories: int
    pinned_count: int
    high_importance_count: int
    recently_used_count: int
    category_distribution: dict
    importance_distribution: dict
    most_used_category: Optional[str] = None
    oldest_memory_date: Optional[datetime] = None
    newest_memory_date: Optional[datetime] = None


class MentorMemorySettings(BaseModel):
    """User memory preferences & configuration."""

    memory_enabled: bool = True
    automatic_extraction: bool = True
    automatic_updates: bool = True
    memory_notifications: bool = True


class MentorMemorySettingsUpdate(BaseModel):
    """Partial update payload for user memory settings."""

    memory_enabled: Optional[bool] = None
    automatic_extraction: Optional[bool] = None
    automatic_updates: Optional[bool] = None
    memory_notifications: Optional[bool] = None


# ──────────────────────────────────────────────────────────────────────────────
# Filter params
# ──────────────────────────────────────────────────────────────────────────────

class MemoryFilterParams(BaseModel):
    """Query parameters for GET /mentor/memory."""

    category: Optional[MemoryCategory] = None
    importance: Optional[MemoryImportance] = None
    status: Optional[MemoryStatus] = MemoryStatus.ACTIVE
    search: Optional[str] = Field(default=None, max_length=255)
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)

