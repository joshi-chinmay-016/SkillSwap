"""
MentorMemoryService — business logic for long-term AI memory.

Responsibilities:
    - Ownership validation
    - CRUD operations (delegating persistence to MentorMemoryRepository)
    - Duplicate detection (normalized title comparison)
    - Archive / status management
    - Triggering memory extraction
    - Logging and metrics

Business logic belongs here. Repository handles persistence only.
"""
import logging
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.mentor_memory import MentorMemory, MemoryStatus, MemoryImportance
from app.schemas.mentor_memory import (
    MentorMemoryCreate,
    MentorMemoryUpdate,
    MentorMemoryListResponse,
    MentorMemoryResponse,
    MentorMemoryStatsResponse,
    MentorMemorySettings,
    MentorMemorySettingsUpdate,
    MemoryFilterParams,
)

from app.repositories import mentor_memory_repository as memory_repo

logger = logging.getLogger(__name__)

# ── Metrics (lightweight counters) ────────────────────────────────────────────
_metrics: dict = {
    "total_created": 0,
    "total_archived": 0,
    "total_updated": 0,
    "total_deleted": 0,
    "duplicates_prevented": 0,
    "extractions_triggered": 0,
}


def get_metrics() -> dict:
    """Return a copy of current memory metrics."""
    return dict(_metrics)


# ──────────────────────────────────────────────────────────────────────────────
# CRUD helpers
# ──────────────────────────────────────────────────────────────────────────────

def _normalize_title(title: str) -> str:
    """Normalize a title for duplicate detection: lowercase + strip."""
    return title.strip().lower()


def _is_duplicate(db: Session, user_id: int, title: str) -> Optional[MentorMemory]:
    """
    Simple duplicate detection — compare normalized titles.
    Returns the existing memory if a match is found, else None.
    No embeddings; pure string comparison.
    """
    normalized = _normalize_title(title)
    return memory_repo.find_similar_title(
        db=db,
        user_id=user_id,
        normalized_title=normalized,
    )


def _get_or_404(db: Session, memory_id: int) -> MentorMemory:
    memory = memory_repo.get_memory(db, memory_id)
    if not memory:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Memory {memory_id} not found",
        )
    return memory


def _assert_ownership(memory: MentorMemory, user_id: int) -> None:
    if memory.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this memory",
        )


# ──────────────────────────────────────────────────────────────────────────────
# Public service functions
# ──────────────────────────────────────────────────────────────────────────────

def create_memory(
    db: Session,
    user_id: int,
    data: MentorMemoryCreate,
) -> MentorMemory:
    """
    Validate, deduplicate, then persist a new memory.

    Raises 409 Conflict if an identical (normalized) title already exists for this user.
    """
    # Duplicate detection
    duplicate = _is_duplicate(db, user_id, data.title)
    if duplicate:
        _metrics["duplicates_prevented"] += 1
        logger.info(
            "Memory duplicate prevented for user_id=%d title=%r (existing id=%d)",
            user_id,
            data.title,
            duplicate.id,
        )
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"A memory with a similar title already exists (id={duplicate.id}). "
                "Update the existing memory instead."
            ),
        )

    importance = data.importance.value if data.importance else settings.MEMORY_DEFAULT_IMPORTANCE

    try:
        memory = memory_repo.create_memory(
            db=db,
            user_id=user_id,
            category=data.category.value,
            title=data.title,
            content=data.content,
            importance=importance,
            source=data.source.value,
            is_pinned=data.is_pinned,
        )
        db.commit()
        db.refresh(memory)
        _metrics["total_created"] += 1
        logger.info(
            "Memory created: id=%d user_id=%d category=%s importance=%s",
            memory.id,
            user_id,
            memory.category,
            memory.importance,
        )
        return memory
    except HTTPException:
        db.rollback()
        raise
    except Exception as exc:
        db.rollback()
        logger.error("Failed to create memory for user_id=%d: %s", user_id, str(exc))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create memory: {str(exc)}",
        )


def get_memory_or_404(
    db: Session,
    memory_id: int,
    user_id: int,
) -> MentorMemory:
    """Retrieve a memory, asserting ownership. Raises 404/403 on failure."""
    memory = _get_or_404(db, memory_id)
    _assert_ownership(memory, user_id)
    return memory


def list_memories(
    db: Session,
    user_id: int,
    filters: MemoryFilterParams,
) -> MentorMemoryListResponse:
    """Return paginated, filtered memories for a user."""
    memories, total = memory_repo.list_user_memories(
        db=db,
        user_id=user_id,
        page=filters.page,
        page_size=filters.page_size,
        category=filters.category.value if filters.category else None,
        importance=filters.importance.value if filters.importance else None,
        status=filters.status.value if filters.status else None,
        search=filters.search,
    )
    items = [MentorMemoryResponse.model_validate(m) for m in memories]
    return MentorMemoryListResponse(
        memories=items,
        total=total,
        page=filters.page,
        page_size=filters.page_size,
    )


def update_memory(
    db: Session,
    memory_id: int,
    user_id: int,
    data: MentorMemoryUpdate,
) -> MentorMemory:
    """Apply partial updates to a memory after ownership check."""
    memory = get_memory_or_404(db, memory_id, user_id)

    # If title is changing, check for duplicates
    if data.title and _normalize_title(data.title) != _normalize_title(memory.title):
        duplicate = _is_duplicate(db, user_id, data.title)
        if duplicate and duplicate.id != memory_id:
            _metrics["duplicates_prevented"] += 1
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"A memory with this title already exists (id={duplicate.id}).",
            )

    update_fields = data.model_dump(exclude_none=True)
    # Convert enum values to strings for storage
    for key in ("category", "importance", "source"):
        if key in update_fields and hasattr(update_fields[key], "value"):
            update_fields[key] = update_fields[key].value

    try:
        memory_repo.update_memory(db, memory, **update_fields)
        db.commit()
        db.refresh(memory)
        _metrics["total_updated"] += 1
        logger.info("Memory updated: id=%d user_id=%d", memory_id, user_id)
        return memory
    except HTTPException:
        db.rollback()
        raise
    except Exception as exc:
        db.rollback()
        logger.error("Failed to update memory id=%d: %s", memory_id, str(exc))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update memory: {str(exc)}",
        )


def archive_memory(
    db: Session,
    memory_id: int,
    user_id: int,
) -> MentorMemory:
    """Archive a memory (ACTIVE → ARCHIVED). Archived memories are ignored during retrieval."""
    memory = get_memory_or_404(db, memory_id, user_id)
    if memory.status == MemoryStatus.ARCHIVED.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Memory is already archived",
        )
    try:
        memory_repo.archive_memory(db, memory)
        db.commit()
        db.refresh(memory)
        _metrics["total_archived"] += 1
        logger.info("Memory archived: id=%d user_id=%d", memory_id, user_id)
        return memory
    except HTTPException:
        db.rollback()
        raise
    except Exception as exc:
        db.rollback()
        logger.error("Failed to archive memory id=%d: %s", memory_id, str(exc))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to archive memory: {str(exc)}",
        )


def delete_memory(
    db: Session,
    memory_id: int,
    user_id: int,
) -> None:
    """Permanently delete a memory after ownership check."""
    memory = get_memory_or_404(db, memory_id, user_id)
    try:
        memory_repo.delete_memory(db, memory)
        db.commit()
        _metrics["total_deleted"] += 1
        logger.info("Memory deleted: id=%d user_id=%d", memory_id, user_id)
    except HTTPException:
        db.rollback()
        raise
    except Exception as exc:
        db.rollback()
        logger.error("Failed to delete memory id=%d: %s", memory_id, str(exc))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete memory: {str(exc)}",
        )


def bulk_create_memories(
    db: Session,
    user_id: int,
    candidates: List[MentorMemoryCreate],
) -> List[MentorMemory]:
    """
    Create multiple memories from extraction results.
    Skips duplicates silently (does not raise on conflict).

    Used by MemoryExtractionService after conversation completion.
    """
    created = []
    for candidate in candidates:
        duplicate = _is_duplicate(db, user_id, candidate.title)
        if duplicate:
            _metrics["duplicates_prevented"] += 1
            logger.debug(
                "Bulk create skipped duplicate title=%r user_id=%d", candidate.title, user_id
            )
            continue

        importance = (
            candidate.importance.value if candidate.importance
            else settings.MEMORY_DEFAULT_IMPORTANCE
        )

        try:
            memory = memory_repo.create_memory(
                db=db,
                user_id=user_id,
                category=candidate.category.value,
                title=candidate.title,
                content=candidate.content,
                importance=importance,
                source=candidate.source.value,
                is_pinned=candidate.is_pinned,
            )
            created.append(memory)
            _metrics["total_created"] += 1
        except Exception as exc:
            logger.warning("Bulk create failed for title=%r: %s", candidate.title, str(exc))
            continue

    try:
        db.commit()
        for m in created:
            db.refresh(m)
    except Exception as exc:
        db.rollback()
        logger.error("Bulk commit failed for user_id=%d: %s", user_id, str(exc))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to persist extracted memories: {str(exc)}",
        )

    logger.info(
        "Bulk memory creation: user_id=%d candidates=%d created=%d",
        user_id, len(candidates), len(created),
    )
    return created


def get_active_memories(
    db: Session,
    user_id: int,
) -> List[MentorMemory]:
    """Return all active memories for a user (used internally by retrieval)."""
    return memory_repo.get_active_memories(db, user_id)


def toggle_pin_memory(
    db: Session,
    memory_id: int,
    user_id: int,
    is_pinned: Optional[bool] = None,
) -> MentorMemory:
    """Toggle or update pin status of a memory."""
    memory = get_memory_or_404(db, memory_id, user_id)
    new_pinned = not memory.is_pinned if is_pinned is None else is_pinned
    memory_repo.update_memory(db, memory, is_pinned=new_pinned)
    db.commit()
    db.refresh(memory)
    logger.info("Memory pin updated: id=%d user_id=%d is_pinned=%s", memory_id, user_id, new_pinned)
    return memory


def get_memory_stats(
    db: Session,
    user_id: int,
) -> MentorMemoryStatsResponse:
    """Calculate aggregated memory statistics for a learner from backend database records."""
    all_memories, _ = memory_repo.list_user_memories(db=db, user_id=user_id, page=1, page_size=1000)

    total_memories = len(all_memories)
    pinned_count = sum(1 for m in all_memories if m.is_pinned)
    high_importance_count = sum(1 for m in all_memories if m.importance in (MemoryImportance.HIGH.value, MemoryImportance.CRITICAL.value))
    recently_used_count = sum(1 for m in all_memories if m.last_used_at is not None)

    category_counts: dict = {}
    importance_counts: dict = {}
    category_used_counts: dict = {}

    oldest_date = None
    newest_date = None

    for m in all_memories:
        cat = m.category
        imp = m.importance
        category_counts[cat] = category_counts.get(cat, 0) + 1
        importance_counts[imp] = importance_counts.get(imp, 0) + 1

        if m.last_used_at:
            category_used_counts[cat] = category_used_counts.get(cat, 0) + 1

        if oldest_date is None or m.created_at < oldest_date:
            oldest_date = m.created_at
        if newest_date is None or m.created_at > newest_date:
            newest_date = m.created_at

    most_used_category = None
    if category_used_counts:
        most_used_category = max(category_used_counts, key=category_used_counts.get)
    elif category_counts:
        most_used_category = max(category_counts, key=category_counts.get)

    return MentorMemoryStatsResponse(
        total_memories=total_memories,
        pinned_count=pinned_count,
        high_importance_count=high_importance_count,
        recently_used_count=recently_used_count,
        category_distribution=category_counts,
        importance_distribution=importance_counts,
        most_used_category=most_used_category,
        oldest_memory_date=oldest_date,
        newest_memory_date=newest_date,
    )


# Store memory settings per user (in-memory persistent state)
_user_memory_settings: dict = {}


def get_memory_settings(
    db: Session,
    user_id: int,
) -> MentorMemorySettings:
    """Return memory configuration for the given user."""
    if user_id not in _user_memory_settings:
        _user_memory_settings[user_id] = MentorMemorySettings()
    return _user_memory_settings[user_id]


def update_memory_settings(
    db: Session,
    user_id: int,
    data: MentorMemorySettingsUpdate,
) -> MentorMemorySettings:
    """Update memory configuration for the given user."""
    current = get_memory_settings(db, user_id)
    updated_dict = current.model_dump()
    patch_data = data.model_dump(exclude_none=True)
    updated_dict.update(patch_data)
    new_settings = MentorMemorySettings(**updated_dict)
    _user_memory_settings[user_id] = new_settings
    logger.info("Memory settings updated for user_id=%d: %s", user_id, patch_data)
    return new_settings

