"""
MemoryRetrievalService — selects the most relevant long-term memories for a mentor turn.

Responsibilities:
    - Load all active memories for a user
    - Score each memory against the current question
    - Rank memories by relevance
    - Respect configurable limit and pinned priority
    - Return formatted mentor-friendly context strings

No embeddings, no semantic search.
Deterministic scoring based on: category, keyword overlap, importance, recency.

Day 65 Part A2 — retrieval pipeline.
"""
import logging
import time
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from typing import List, Optional

from app.core.config import settings
from app.models.mentor_memory import MentorMemory, MemoryImportance, MemoryCategory
from app.repositories import mentor_memory_repository as memory_repo
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

# ── Metrics ────────────────────────────────────────────────────────────────────
_metrics: dict = {
    "total_retrievals": 0,
    "total_memories_retrieved": 0,
    "total_latency_ms": 0.0,
}


def get_retrieval_metrics() -> dict:
    return dict(_metrics)


# ── Importance weight map ──────────────────────────────────────────────────────
_IMPORTANCE_SCORE = {
    MemoryImportance.LOW.value: 0.25,
    MemoryImportance.MEDIUM.value: 0.50,
    MemoryImportance.HIGH.value: 0.75,
    MemoryImportance.CRITICAL.value: 1.0,
}

# ── Category to keyword signals ─────────────────────────────────────────────────
_CATEGORY_KEYWORDS: dict[str, List[str]] = {
    MemoryCategory.LEARNING_STYLE.value: ["learn", "style", "explain", "understand"],
    MemoryCategory.LONG_TERM_GOAL.value: ["goal", "career", "become", "aspire", "future"],
    MemoryCategory.STRONG_TOPIC.value: ["strong", "good at", "comfortable", "confident"],
    MemoryCategory.WEAK_TOPIC.value: ["struggle", "difficult", "hard", "weak", "confuse"],
    MemoryCategory.LEARNING_PREFERENCE.value: ["prefer", "like", "rather", "easier", "better"],
    MemoryCategory.FREQUENT_TOPIC.value: ["often", "frequently", "always", "again"],
    MemoryCategory.ACHIEVEMENT.value: ["achieved", "completed", "mastered", "finished"],
    MemoryCategory.PERSONAL_PREFERENCE.value: ["prefer", "like", "want"],
    MemoryCategory.GENERAL.value: [],
}


@dataclass
class ScoredMemory:
    memory: MentorMemory
    score: float


class MemoryRetrievalService:
    """
    Single entry point for mentor memory retrieval.

    Usage:
        service = MemoryRetrievalService()
        retrieved = service.retrieve(db, user_id, question)
        # Returns formatted strings ready for prompt injection
    """

    def retrieve(
        self,
        db: Session,
        user_id: int,
        question: str,
        max_memories: Optional[int] = None,
    ) -> List[MentorMemory]:
        """
        Retrieve the most relevant active memories for a given question.

        Parameters
        ----------
        db           : SQLAlchemy session
        user_id      : authenticated user (privacy enforced — only their memories)
        question     : the current learner question used for relevance scoring
        max_memories : override the config default (MEMORY_MAX_RETRIEVED)

        Returns
        -------
        List of MentorMemory ORM objects, ranked by relevance, bounded by max_memories.
        """
        t0 = time.perf_counter()
        limit = max_memories or settings.MEMORY_MAX_RETRIEVED

        all_memories = memory_repo.get_active_memories(db, user_id)
        if not all_memories:
            return []

        scored = [
            ScoredMemory(memory=m, score=self._score(m, question))
            for m in all_memories
        ]
        scored.sort(key=lambda s: s.score, reverse=True)

        top = [s.memory for s in scored[:limit]]

        latency_ms = (time.perf_counter() - t0) * 1000
        _metrics["total_retrievals"] += 1
        _metrics["total_memories_retrieved"] += len(top)
        _metrics["total_latency_ms"] += latency_ms

        logger.info(
            "MemoryRetrievalService: user_id=%d candidates=%d retrieved=%d latency=%.1fms",
            user_id, len(all_memories), len(top), latency_ms,
        )
        return top

    def format_for_prompt(self, memories: List[MentorMemory]) -> str:
        """
        Convert a list of memories into a mentor-friendly prompt section.

        Does NOT dump raw database rows — produces natural language sentences.
        """
        if not memories:
            return ""

        lines = ["[Long-Term Memory — What I Remember About This Learner]"]
        for m in memories:
            lines.append(f"- {m.content}")
        return "\n".join(lines)

    # ──────────────────────────────────────────────────────────────────────────
    # Scoring
    # ──────────────────────────────────────────────────────────────────────────

    def _score(self, memory: MentorMemory, question: str) -> float:
        """
        Compute a relevance score for a single memory against the current question.

        Score components (configurable via settings):
            - importance_score  × MEMORY_WEIGHT_IMPORTANCE
            - category_score    × MEMORY_WEIGHT_CATEGORY
            - keyword_score     × MEMORY_WEIGHT_KEYWORD
            - recency_bonus     × MEMORY_WEIGHT_RECENCY

        Pinned memories receive an extra MEMORY_PINNED_PRIORITY_BONUS.
        """
        w_importance = settings.MEMORY_WEIGHT_IMPORTANCE
        w_category = settings.MEMORY_WEIGHT_CATEGORY
        w_keyword = settings.MEMORY_WEIGHT_KEYWORD
        w_recency = settings.MEMORY_WEIGHT_RECENCY

        importance_score = _IMPORTANCE_SCORE.get(memory.importance, 0.5)
        category_score = self._category_relevance(memory.category, question)
        keyword_score = self._keyword_overlap(memory, question)
        recency_score = self._recency_score(memory)

        raw = (
            importance_score * w_importance
            + category_score * w_category
            + keyword_score * w_keyword
            + recency_score * w_recency
        )

        if memory.is_pinned:
            raw += settings.MEMORY_PINNED_PRIORITY_BONUS

        return raw

    @staticmethod
    def _category_relevance(category: str, question: str) -> float:
        """Score 0–1 based on whether question keywords align with category signals."""
        signals = _CATEGORY_KEYWORDS.get(category, [])
        if not signals:
            return 0.1
        question_lower = question.lower()
        matches = sum(1 for kw in signals if kw in question_lower)
        return min(1.0, matches / max(len(signals), 1))

    @staticmethod
    def _keyword_overlap(memory: MentorMemory, question: str) -> float:
        """
        Score 0–1 based on word overlap between memory title/content and question.
        Simple bag-of-words, no TF-IDF.
        """
        stop_words = {"the", "a", "an", "is", "are", "was", "were", "i", "me", "my",
                      "you", "your", "we", "it", "to", "of", "and", "or", "in", "on",
                      "at", "for", "with", "that", "this", "be", "can", "do", "did"}

        question_words = {
            w.lower() for w in question.split()
            if len(w) > 2 and w.lower() not in stop_words
        }
        if not question_words:
            return 0.0

        memory_text = f"{memory.title} {memory.content}".lower()
        memory_words = {w for w in memory_text.split() if len(w) > 2 and w not in stop_words}

        overlap = question_words & memory_words
        return min(1.0, len(overlap) / max(len(question_words), 1))

    @staticmethod
    def _recency_score(memory: MentorMemory) -> float:
        """
        Score 0–1 based on how recently the memory was used or created.
        Recent = higher score; older than MEMORY_DECAY_DAYS = 0.
        """
        now = datetime.now(timezone.utc)
        reference = memory.last_used_at or memory.created_at
        # Ensure timezone aware
        if reference.tzinfo is None:
            reference = reference.replace(tzinfo=timezone.utc)

        age_days = (now - reference).days
        decay_days = max(settings.MEMORY_DECAY_DAYS, 1)

        if age_days >= decay_days:
            return 0.0
        return 1.0 - (age_days / decay_days)
