"""
MemoryUpdateService — evolves existing memories over time.

Responsibilities:
    - Refresh last_used_at after retrieval
    - Update/bump importance when a memory is re-confirmed
    - Merge similar memories (avoid duplicates from multiple extractions)
    - Archive memories that have decayed (not used for MEMORY_DECAY_DAYS)
    - Conflict resolution (replace vs. archive old memory when values change)

Day 65 Part A2 — memory evolution pipeline.
"""
import logging
from datetime import datetime, timezone, timedelta
from typing import List, Optional

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.mentor_memory import MentorMemory, MemoryStatus, MemoryImportance
from app.repositories import mentor_memory_repository as memory_repo

logger = logging.getLogger(__name__)

# ── Importance escalation order ────────────────────────────────────────────────
_IMPORTANCE_ORDER = [
    MemoryImportance.LOW.value,
    MemoryImportance.MEDIUM.value,
    MemoryImportance.HIGH.value,
    MemoryImportance.CRITICAL.value,
]

# ── Metrics ────────────────────────────────────────────────────────────────────
_metrics: dict = {
    "total_refreshed": 0,
    "total_importance_bumped": 0,
    "total_merged": 0,
    "total_decayed": 0,
    "total_conflicts_resolved": 0,
}


def get_update_metrics() -> dict:
    return dict(_metrics)


class MemoryUpdateService:
    """
    Manages memory evolution after each mentor interaction.

    Usage (called from AIMentorService after response generation):
        update_service = MemoryUpdateService()
        update_service.refresh_used_memories(db, used_memories)
        update_service.run_decay_check(db, user_id)
    """

    def refresh_used_memories(
        self,
        db: Session,
        memories: List[MentorMemory],
    ) -> None:
        """
        Update last_used_at for every memory that participated in a response.
        Must be called after db.commit() in the mentor pipeline.
        """
        if not memories:
            return

        now = datetime.now(timezone.utc)
        try:
            for memory in memories:
                memory_repo.touch_last_used(db, memory, now)
            db.commit()
            _metrics["total_refreshed"] += len(memories)
            logger.debug(
                "MemoryUpdateService: refreshed last_used_at for %d memories", len(memories)
            )
        except Exception as exc:
            db.rollback()
            logger.error("MemoryUpdateService: failed to refresh memories: %s", str(exc))

    def bump_importance(
        self,
        db: Session,
        memory: MentorMemory,
    ) -> MentorMemory:
        """
        Escalate a memory's importance by one level (if not already CRITICAL).
        Used when the same fact is re-confirmed across conversations.
        """
        current_idx = _IMPORTANCE_ORDER.index(memory.importance) if memory.importance in _IMPORTANCE_ORDER else 1
        if current_idx < len(_IMPORTANCE_ORDER) - 1:
            new_importance = _IMPORTANCE_ORDER[current_idx + 1]
            try:
                memory_repo.update_memory(db, memory, importance=new_importance)
                db.commit()
                db.refresh(memory)
                _metrics["total_importance_bumped"] += 1
                logger.info(
                    "MemoryUpdateService: importance bumped id=%d %s→%s",
                    memory.id, memory.importance, new_importance,
                )
            except Exception as exc:
                db.rollback()
                logger.error("Failed to bump importance for memory id=%d: %s", memory.id, str(exc))
        return memory

    def merge_memories(
        self,
        db: Session,
        primary: MentorMemory,
        secondary: MentorMemory,
    ) -> MentorMemory:
        """
        Merge two similar memories: archive the secondary, enrich the primary.

        The primary keeps its id. Secondary is archived, not deleted.
        """
        try:
            # Combine content if different
            if secondary.content.strip() not in primary.content:
                merged_content = f"{primary.content.rstrip('.')}. {secondary.content}"
                memory_repo.update_memory(db, primary, content=merged_content[:2000])

            # Take the higher importance
            primary_idx = _IMPORTANCE_ORDER.index(primary.importance) if primary.importance in _IMPORTANCE_ORDER else 1
            secondary_idx = _IMPORTANCE_ORDER.index(secondary.importance) if secondary.importance in _IMPORTANCE_ORDER else 1
            if secondary_idx > primary_idx:
                memory_repo.update_memory(db, primary, importance=secondary.importance)

            # Archive the secondary
            memory_repo.archive_memory(db, secondary)
            db.commit()
            db.refresh(primary)

            _metrics["total_merged"] += 1
            logger.info(
                "MemoryUpdateService: merged memory id=%d (secondary id=%d archived)",
                primary.id, secondary.id,
            )
            return primary
        except Exception as exc:
            db.rollback()
            logger.error(
                "Failed to merge memories primary=%d secondary=%d: %s",
                primary.id, secondary.id, str(exc),
            )
            raise

    def run_decay_check(
        self,
        db: Session,
        user_id: int,
    ) -> int:
        """
        Archive memories that have not been used for MEMORY_DECAY_DAYS.
        Returns the number of memories archived.

        Safe to run periodically — does not delete anything.
        """
        cutoff = datetime.now(timezone.utc) - timedelta(days=settings.MEMORY_DECAY_DAYS)
        active_memories = memory_repo.get_active_memories(db, user_id)

        archived_count = 0
        for memory in active_memories:
            reference = memory.last_used_at or memory.created_at
            if reference.tzinfo is None:
                reference = reference.replace(tzinfo=timezone.utc)
            if reference < cutoff and not memory.is_pinned:
                try:
                    memory_repo.archive_memory(db, memory)
                    archived_count += 1
                    _metrics["total_decayed"] += 1
                    logger.info(
                        "MemoryUpdateService: decayed memory id=%d (last_used=%s)",
                        memory.id, reference.date(),
                    )
                except Exception as exc:
                    logger.warning("Failed to decay memory id=%d: %s", memory.id, str(exc))

        if archived_count:
            try:
                db.commit()
                logger.info(
                    "MemoryUpdateService: decay run complete — archived %d memories for user_id=%d",
                    archived_count, user_id,
                )
            except Exception as exc:
                db.rollback()
                logger.error("Failed to commit decay changes for user_id=%d: %s", user_id, str(exc))

        return archived_count

    def resolve_conflict(
        self,
        db: Session,
        old_memory: MentorMemory,
        new_content: str,
        action: str = "merge",
    ) -> MentorMemory:
        """
        Handle conflicting memory facts.

        action options:
            'merge'   — combine old and new content (default)
            'replace' — replace old content with new content
            'archive' — archive old memory (keeps new separately)
        """
        if action == "replace":
            memory_repo.update_memory(db, old_memory, content=new_content)
            db.commit()
            db.refresh(old_memory)
        elif action == "archive":
            memory_repo.archive_memory(db, old_memory)
            db.commit()
        else:  # merge
            if new_content.strip() not in old_memory.content:
                merged = f"{old_memory.content.rstrip('.')}. {new_content}"
                memory_repo.update_memory(db, old_memory, content=merged[:2000])
                db.commit()
                db.refresh(old_memory)

        _metrics["total_conflicts_resolved"] += 1
        logger.info(
            "MemoryUpdateService: conflict resolved id=%d action=%s",
            old_memory.id, action,
        )
        return old_memory
