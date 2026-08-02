"""
API Router for Long-Term AI Memory Management (Day 65 Part B).

Prefix: /mentor/memory
Tags: AI Long-Term Memory
"""
from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.dependencies.current_user import get_current_user
from app.models.user import User
from app.models.mentor_memory import MemoryCategory, MemoryImportance, MemoryStatus
from app.schemas.mentor_memory import (
    MentorMemoryCreate,
    MentorMemoryUpdate,
    MentorMemoryResponse,
    MentorMemoryListResponse,
    MentorMemoryStatsResponse,
    MentorMemorySettings,
    MentorMemorySettingsUpdate,
    MemoryFilterParams,
)
from app.services import mentor_memory_service as service

router = APIRouter(
    prefix="/mentor/memory",
    tags=["AI Long-Term Memory"],
)


@router.post(
    "",
    response_model=MentorMemoryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new long-term AI memory record",
)
def create_memory(
    data: MentorMemoryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    memory = service.create_memory(db=db, user_id=current_user.id, data=data)
    return MentorMemoryResponse.model_validate(memory)


@router.get(
    "",
    response_model=MentorMemoryListResponse,
    summary="List paginated, filtered memories for the authenticated user",
)
def list_memories(
    category: Optional[MemoryCategory] = Query(default=None, description="Filter by category"),
    importance: Optional[MemoryImportance] = Query(default=None, description="Filter by importance"),
    status_filter: Optional[MemoryStatus] = Query(default=MemoryStatus.ACTIVE, alias="status", description="Filter by status (ACTIVE, ARCHIVED)"),
    search: Optional[str] = Query(default=None, max_length=255, description="Search term for title or content"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    filters = MemoryFilterParams(
        category=category,
        importance=importance,
        status=status_filter,
        search=search,
        page=page,
        page_size=page_size,
    )
    return service.list_memories(db=db, user_id=current_user.id, filters=filters)


@router.get(
    "/stats",
    response_model=MentorMemoryStatsResponse,
    summary="Get memory metrics dashboard summary and distributions",
)
def get_memory_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return service.get_memory_stats(db=db, user_id=current_user.id)


@router.get(
    "/settings",
    response_model=MentorMemorySettings,
    summary="Get user memory configuration settings",
)
def get_memory_settings(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return service.get_memory_settings(db=db, user_id=current_user.id)


@router.patch(
    "/settings",
    response_model=MentorMemorySettings,
    summary="Update user memory configuration settings",
)
def update_memory_settings(
    data: MentorMemorySettingsUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return service.update_memory_settings(db=db, user_id=current_user.id, data=data)


@router.get(
    "/{memory_id}",
    response_model=MentorMemoryResponse,
    summary="Get single memory details by ID",
)
def get_memory(
    memory_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    memory = service.get_memory_or_404(db=db, memory_id=memory_id, user_id=current_user.id)
    return MentorMemoryResponse.model_validate(memory)


@router.patch(
    "/{memory_id}",
    response_model=MentorMemoryResponse,
    summary="Update memory title, content, importance, or category",
)
def update_memory(
    memory_id: int,
    data: MentorMemoryUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    memory = service.update_memory(db=db, memory_id=memory_id, user_id=current_user.id, data=data)
    return MentorMemoryResponse.model_validate(memory)


@router.post(
    "/{memory_id}/archive",
    response_model=MentorMemoryResponse,
    summary="Archive a memory so it will no longer be used for AI context",
)

@router.patch(
    "/{memory_id}/archive",
    response_model=MentorMemoryResponse,
    summary="Archive a memory so it will no longer be used for AI context",
)
def archive_memory(
    memory_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    memory = service.archive_memory(db=db, memory_id=memory_id, user_id=current_user.id)
    return MentorMemoryResponse.model_validate(memory)


@router.patch(
    "/{memory_id}/pin",
    response_model=MentorMemoryResponse,
    summary="Toggle or set pin status of a memory for priority retrieval",
)
def toggle_pin_memory(
    memory_id: int,
    is_pinned: Optional[bool] = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    memory = service.toggle_pin_memory(db=db, memory_id=memory_id, user_id=current_user.id, is_pinned=is_pinned)
    return MentorMemoryResponse.model_validate(memory)


@router.delete(
    "/{memory_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Permanently forget/delete a memory",
)
def delete_memory(
    memory_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service.delete_memory(db=db, memory_id=memory_id, user_id=current_user.id)
    return None
