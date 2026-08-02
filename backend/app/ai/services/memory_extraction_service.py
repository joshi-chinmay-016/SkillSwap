"""
MemoryExtractionService — analyzes completed conversations to extract long-term memories.

Responsibilities:
    - Analyze conversation message history
    - Apply extraction rules (what is durable vs. temporary)
    - Return structured MentorMemoryCreate candidates

Does NOT store memories directly.
Storage belongs to MentorMemoryService.bulk_create_memories().

Day 65 Part A1 — extraction pipeline.
"""
import logging
import re
from typing import List

from app.core.config import settings
from app.models.mentor_memory import MemoryCategory, MemoryImportance, MemorySource
from app.schemas.mentor_memory import MentorMemoryCreate

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────────────────────────────────────
# Extraction rule patterns
# ──────────────────────────────────────────────────────────────────────────────

# Phrases that suggest a durable learning style / preference
_STYLE_SIGNALS = [
    (r"\b(always|better|best|prefer|rather|easier|more clearly)\b.*\b(diagram|visual|picture|draw)\b",
     MemoryCategory.LEARNING_PREFERENCE, "Prefers visual/diagram explanations", MemoryImportance.HIGH),
    (r"\bprefer(s)?\b.*\b(code|example|implementation|hands.?on)\b",
     MemoryCategory.LEARNING_STYLE, "Prefers implementation-first learning", MemoryImportance.HIGH),
    (r"\blearn(s)?\s+(better|best|faster)\b.*\b(analogy|analogi|story|example)\b",
     MemoryCategory.LEARNING_STYLE, "Learns better through analogies", MemoryImportance.HIGH),
    (r"\bwant(s)?\s+to\s+(be|become|work as|get a job|career)\b.*\b(engineer|developer|scientist|architect|designer)\b",
     MemoryCategory.LONG_TERM_GOAL, "Career goal identified", MemoryImportance.CRITICAL),
    (r"\b(goal|target|aim|aspire)\b.{0,60}\b(backend|frontend|fullstack|data|ml|ai|devops|cloud)\b",
     MemoryCategory.LONG_TERM_GOAL, "Technical specialisation goal", MemoryImportance.HIGH),
    (r"\b(always|keep|consistently|often|struggle|difficult|hard)\b.{0,60}\b(with|for|on)\b.{0,60}\b\w+\b",
     MemoryCategory.WEAK_TOPIC, "Persistent struggle identified", MemoryImportance.HIGH),
    (r"\b(comfortable|confident|strong|already know|mastered|understand well)\b.{0,60}\b\w+\b",
     MemoryCategory.STRONG_TOPIC, "Strong topic identified", MemoryImportance.MEDIUM),
]

# Signals that indicate the content is temporary / not durable
_IGNORE_PATTERNS = [
    r"^\s*(hi|hello|hey|thanks|thank you|ok|okay|great|sure|yes|no|bye|goodbye)\s*$",
    r"^.{0,30}$",  # very short messages — unlikely to carry durable facts
    r"\b(today|right now|currently|at the moment|for now)\b",  # temporary state signals
]


# ──────────────────────────────────────────────────────────────────────────────
# Service
# ──────────────────────────────────────────────────────────────────────────────

class MemoryExtractionService:
    """
    Analyzes a conversation to extract durable learner facts.

    Usage:
        service = MemoryExtractionService()
        candidates = service.extract_from_conversation(messages)
        # Then pass candidates to MentorMemoryService.bulk_create_memories()
    """

    def extract_from_conversation(
        self,
        messages: list,
        max_candidates: int = 10,
    ) -> List[MentorMemoryCreate]:
        """
        Analyze conversation messages and return candidate memories.

        Parameters
        ----------
        messages        : list of MentorMessage ORM objects (role + content)
        max_candidates  : hard cap on returned candidates per conversation

        Returns
        -------
        List of MentorMemoryCreate — caller is responsible for deduplication + persistence.
        """
        if not settings.MEMORY_EXTRACTION_ENABLED:
            logger.debug("Memory extraction disabled by config — skipping")
            return []

        logger.info("MemoryExtractionService: analyzing %d messages", len(messages))

        candidates: List[MentorMemoryCreate] = []
        seen_titles: set = set()

        # Only look at USER messages — they carry learner facts
        user_messages = [m for m in messages if m.role.upper() == "USER"]

        for msg in user_messages:
            text = msg.content.strip()

            # Skip small-talk / temporary content
            if self._is_ignorable(text):
                continue

            # Apply extraction rules
            extracted = self._apply_rules(text)
            for candidate in extracted:
                norm_title = candidate.title.lower()
                if norm_title in seen_titles:
                    continue
                seen_titles.add(norm_title)
                candidates.append(candidate)
                if len(candidates) >= max_candidates:
                    break

            if len(candidates) >= max_candidates:
                break

        logger.info(
            "MemoryExtractionService: extracted %d candidates from %d user messages",
            len(candidates),
            len(user_messages),
        )
        return candidates

    # ──────────────────────────────────────────────────────────────────────────
    # Private helpers
    # ──────────────────────────────────────────────────────────────────────────

    def _is_ignorable(self, text: str) -> bool:
        """Return True if the message is unlikely to contain durable facts."""
        for pattern in _IGNORE_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        return False

    def _apply_rules(self, text: str) -> List[MentorMemoryCreate]:
        """Match extraction rules against a message and return candidates."""
        results = []
        for pattern, category, title_template, importance in _STYLE_SIGNALS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                # Build a human-readable content from the matched message
                content = self._summarize_content(text, category)
                results.append(
                    MentorMemoryCreate(
                        category=category,
                        title=title_template,
                        content=content,
                        importance=importance,
                        source=MemorySource.CONVERSATION,
                        is_pinned=False,
                    )
                )
        return results

    @staticmethod
    def _summarize_content(text: str, category: MemoryCategory) -> str:
        """Create a short content string from the original message."""
        # Truncate long messages for storage
        max_len = 500
        summary = text[:max_len].strip()
        if len(text) > max_len:
            summary += "..."
        return summary
