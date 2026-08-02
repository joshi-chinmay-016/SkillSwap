"""
MentorMemoryRepository — database persistence for MentorMemory.

Responsibilities: database queries only.
No business logic, no authorization, no LLM calls.
"""
import logging
from datetime import datetime, timezone
from typing import List, Optional, Tuple

from sqlalchemy.orm import Session

from app.models.mentor_memory import MentorMemory, MemoryCategory, MemoryStatus

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────────────────────────────────────
# Write operations
# ──────────────────────────────────────────────────────────────────────────────

def create_memory(
    db: Session,
    user_id: int,
    category: str,
    title: str,
    content: str,
    importance: str,
    source: str,
    is_pinned: bool = False,
) -> MentorMemory:
    """Persist a new MentorMemory. Caller must commit."""
    memory = MentorMemory(
        user_id=user_id,
        category=category,
        title=title,
        content=content,
        importance=importance,
        source=source,
        status=MemoryStatus.ACTIVE.value,
        is_pinned=is_pinned,
    )
    db.add(memory)
    db.flush()
    return memory


def update_memory(
    db: Session,
    memory: MentorMemory,
    **kwargs,
) -> MentorMemory:
    """
    Apply arbitrary field updates to a memory.
    Caller must commit.

    Accepted kwargs: category, title, content, importance, source, is_pinned
    """
    for field, value in kwargs.items():
        setattr(memory, field, value)
    db.flush()
    return memory


def archive_memory(
    db: Session,
    memory: MentorMemory,
) -> MentorMemory:
    """Set status to ARCHIVED. Caller must commit."""
    memory.status = MemoryStatus.ARCHIVED.value
    db.flush()
    return memory


def delete_memory(
    db: Session,
    memory: MentorMemory,
) -> None:
    """Hard-delete the memory record. Caller must commit."""
    db.delete(memory)
    db.flush()


def touch_last_used(
    db: Session,
    memory: MentorMemory,
    timestamp: Optional[datetime] = None,
) -> MentorMemory:
    """
    Refresh last_used_at timestamp (Part A2 — retrieval tracking).
    Caller must commit.
    """
    memory.last_used_at = timestamp or datetime.now(timezone.utc)
    db.flush()
    return memory


# ──────────────────────────────────────────────────────────────────────────────
# Read operations
# ──────────────────────────────────────────────────────────────────────────────

def get_memory(
    db: Session,
    memory_id: int,
) -> Optional[MentorMemory]:
    """Return a memory by primary key, or None."""
    return (
        db.query(MentorMemory)
        .filter(MentorMemory.id == memory_id)
        .first()
    )


def get_user_memory(
    db: Session,
    memory_id: int,
    user_id: int,
) -> Optional[MentorMemory]:
    """Return a memory only if it belongs to user_id."""
    return (
        db.query(MentorMemory)
        .filter(
            MentorMemory.id == memory_id,
            MentorMemory.user_id == user_id,
        )
        .first()
    )


def list_user_memories(
    db: Session,
    user_id: int,
    page: int = 1,
    page_size: int = 20,
    category: Optional[str] = None,
    importance: Optional[str] = None,
    status: Optional[str] = None,
    search: Optional[str] = None,
) -> Tuple[List[MentorMemory], int]:
    """
    Return paginated memories for a user with optional filters.

    Returns (memories, total_count).
    """
    query = db.query(MentorMemory).filter(MentorMemory.user_id == user_id)

    if category:
        query = query.filter(MentorMemory.category == category.upper())
    if importance:
        query = query.filter(MentorMemory.importance == importance.upper())
    if status:
        query = query.filter(MentorMemory.status == status.upper())
    if search:
        pattern = f"%{search.lower()}%"
        query = query.filter(
            (MentorMemory.title.ilike(pattern)) | (MentorMemory.content.ilike(pattern))
        )

    total = query.count()
    memories = (
        query
        .order_by(
            MentorMemory.is_pinned.desc(),
            MentorMemory.importance.desc(),
            MentorMemory.created_at.desc(),
        )
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return memories, total


def get_active_memories(
    db: Session,
    user_id: int,
) -> List[MentorMemory]:
    """Return all ACTIVE memories for a user — used by retrieval service."""
    return (
        db.query(MentorMemory)
        .filter(
            MentorMemory.user_id == user_id,
            MentorMemory.status == MemoryStatus.ACTIVE.value,
        )
        .order_by(
            MentorMemory.is_pinned.desc(),
            MentorMemory.importance.desc(),
        )
        .all()
    )


def get_by_category(
    db: Session,
    user_id: int,
    category: str,
    status: str = MemoryStatus.ACTIVE.value,
) -> List[MentorMemory]:
    """Return active memories for a user filtered by category."""
    return (
        db.query(MentorMemory)
        .filter(
            MentorMemory.user_id == user_id,
            MentorMemory.category == category,
            MentorMemory.status == status,
        )
        .order_by(MentorMemory.importance.desc(), MentorMemory.created_at.desc())
        .all()
    )


def find_similar_title(
    db: Session,
    user_id: int,
    normalized_title: str,
    status: str = MemoryStatus.ACTIVE.value,
) -> Optional[MentorMemory]:
    """
    Duplicate detection — find an active memory with a matching normalized title.
    Uses simple ilike matching; no embeddings.
    """
    return (
        db.query(MentorMemory)
        .filter(
            MentorMemory.user_id == user_id,
            MentorMemory.status == status,
            MentorMemory.title.ilike(normalized_title),
        )
        .first()
    )
