"""
ContextBuilder — Day 72 Part A1.

Transforms authorized, retrieved chunks into bounded, structured context that
the PromptBuilder can consume.  This is the bridge between the Retriever and
the generation layer.

Pipeline inside DefaultContextBuilder.build():

    RetrievedChunk[]                     (input from Retriever)
          │
          ▼
    Chunk Validation                     (skip malformed, log diagnostics)
          │
          ▼
    Defensive Deduplication              (set-based, keep best-ranked)
          │
          ▼
    Relevance Ordering                   (preserve Retriever rank order)
          │
          ▼
    Context Budgeting                    (chunks, characters, token estimate)
          │
          ▼
    Deterministic Formatting             (<retrieved_context> XML boundaries)
          │
          ▼
    ContextResult                        (output for PromptBuilder)

Design constraints (enforced):
    - Does NOT query FAISS.
    - Does NOT generate embeddings.
    - Does NOT perform authorization (input is already authorized).
    - Does NOT modify the database.
    - Does NOT call the LLM.
    - Does NOT log raw chunk content (private user data).

Token estimation:
    token_estimate = len(text) // 4
    This is a rough approximation (English text averages ~4 chars/token).
    It is NOT exact token accounting.  Do not use it for billing or hard limits
    in production LLM calls that have strict token budgets.

Prompt-injection / data boundary:
    All retrieved content is wrapped inside <retrieved_context> XML tags in
    the formatted output.  This ensures that downstream PromptBuilder can
    clearly delimit user-provided knowledge from application instructions,
    preventing retrieved document text from being mistaken for system
    instructions by the LLM.
"""
from __future__ import annotations

import abc
import logging
import time
from typing import Optional

from app.core.config import settings
from app.rag.context_exceptions import ContextBuildError
from app.rag.context_models import ContextRequest, ContextResult, ContextSource
from app.retrieval.retrieval_models import RetrievedChunk

logger = logging.getLogger(__name__)

# ── Constants ─────────────────────────────────────────────────────────────────

# Approximate chars per token (English prose average).  Used only for estimation.
_CHARS_PER_TOKEN_ESTIMATE = 4

# Minimum content length for a chunk to be considered valid.
_MIN_CONTENT_LENGTH = 1


# ── Abstract base ─────────────────────────────────────────────────────────────


class ContextBuilder(abc.ABC):
    """
    Abstract interface for a context-building implementation.

    Implementations receive authorized retrieved chunks and produce a
    bounded ContextResult ready for the PromptBuilder.

    Implementations must NOT:
        - Query FAISS or any vector store.
        - Generate embeddings.
        - Perform authorization.
        - Modify the database.
        - Call the LLM.
        - Log raw chunk content.
    """

    @abc.abstractmethod
    def build(self, request: ContextRequest) -> ContextResult:
        """
        Build bounded context from authorized retrieved chunks.

        Args:
            request: ContextRequest containing the retrieved chunks and
                     optional per-request budget overrides.

        Returns:
            ContextResult with formatted context, source list, and metrics.

        Raises:
            ContextBuildError: Unexpected internal failure during construction.
        """
        ...


# ── Default implementation ────────────────────────────────────────────────────


class DefaultContextBuilder(ContextBuilder):
    """
    Production-ready ContextBuilder implementation.

    Reads limits from application settings by default.  Per-request overrides
    in ContextRequest take precedence over the settings values.

    Usage::

        builder = DefaultContextBuilder.from_settings()
        result = builder.build(ContextRequest(retrieved_chunks=chunks))
        print(result.context_text)
        print(result.truncated)
    """

    def __init__(
        self,
        *,
        max_chunks: int,
        max_characters: int,
        max_tokens: int,
    ) -> None:
        """
        Args:
            max_chunks     : Default maximum number of chunks to include.
            max_characters : Default maximum character count for context.
            max_tokens     : Default approximate token budget for context.
        """
        self._default_max_chunks = max_chunks
        self._default_max_characters = max_characters
        self._default_max_tokens = max_tokens

    # ── Factory ───────────────────────────────────────────────────────────────

    @classmethod
    def from_settings(cls) -> "DefaultContextBuilder":
        """
        Construct a DefaultContextBuilder from application settings.

        Returns:
            Ready-to-use DefaultContextBuilder.
        """
        return cls(
            max_chunks=getattr(settings, "RAG_MAX_CONTEXT_CHUNKS", 10),
            max_characters=getattr(settings, "RAG_MAX_CONTEXT_CHARACTERS", 12000),
            max_tokens=getattr(settings, "RAG_MAX_CONTEXT_TOKENS", 3000),
        )

    # ── Public interface ──────────────────────────────────────────────────────

    def build(self, request: ContextRequest) -> ContextResult:
        """
        Build bounded context from authorized retrieved chunks.

        Steps:
            1. Resolve per-request budget limits.
            2. Validate each chunk (skip malformed, log diagnostics).
            3. Defensive deduplication by chunk_id (keep best-ranked).
            4. Preserve Retriever relevance ordering (rank ascending).
            5. Apply budget: chunks → characters → token estimate.
            6. Format selected chunks into deterministic XML-bounded text.
            7. Return ContextResult with metrics.

        Args:
            request: ContextRequest with retrieved chunks and optional overrides.

        Returns:
            ContextResult — always valid, even if empty.

        Raises:
            ContextBuildError: Only on unexpected internal failure.
        """
        t_start = time.perf_counter()

        # ── Step 1: Resolve limits ────────────────────────────────────────────
        max_chunks = (
            request.max_chunks
            if request.max_chunks is not None
            else self._default_max_chunks
        )
        max_characters = (
            request.max_characters
            if request.max_characters is not None
            else self._default_max_characters
        )
        max_tokens = (
            request.max_tokens
            if request.max_tokens is not None
            else self._default_max_tokens
        )

        if max_chunks < 1:
            raise ContextBuildError(
                f"max_chunks must be >= 1, got {max_chunks}."
            )
        if max_characters < 1:
            raise ContextBuildError(
                f"max_characters must be >= 1, got {max_characters}."
            )

        # ── Step 2: Validate input chunks ────────────────────────────────────
        valid_chunks = self._validate_chunks(request.retrieved_chunks)

        if not valid_chunks:
            logger.info(
                "ContextBuilder — no valid chunks after validation. "
                "Returning empty context. retrieved=%d",
                len(request.retrieved_chunks),
            )
            return ContextResult(
                context_text="",
                sources=[],
                chunk_count=0,
                character_count=0,
                token_estimate=0,
                truncated=False,
            )

        # ── Step 3: Defensive deduplication by chunk_id ──────────────────────
        deduped = self._deduplicate(valid_chunks)

        # ── Step 4: Preserve relevance ordering (rank ascending = best first) ─
        ordered = sorted(deduped, key=lambda c: (c.rank, c.chunk_id))

        # ── Step 5: Budget selection ──────────────────────────────────────────
        selected, truncated = self._apply_budget(
            ordered,
            max_chunks=max_chunks,
            max_characters=max_characters,
            max_tokens=max_tokens,
        )

        # ── Step 6: Format context text ───────────────────────────────────────
        context_text = self._format_context(selected, include_metadata=request.include_metadata)

        # ── Step 7: Build sources list ────────────────────────────────────────
        sources = [
            ContextSource(
                chunk_id=chunk.chunk_id,
                document_id=chunk.document_id,
                document_name=chunk.document_name,
                rank=chunk.rank,
                score=chunk.score,
            )
            for chunk in selected
        ]

        character_count = len(context_text)
        token_estimate = character_count // _CHARS_PER_TOKEN_ESTIMATE
        duration_ms = (time.perf_counter() - t_start) * 1000

        logger.info(
            "ContextBuilder — build complete: "
            "retrieved=%d valid=%d deduped=%d selected=%d "
            "characters=%d token_estimate=%d truncated=%s duration_ms=%.1f",
            len(request.retrieved_chunks),
            len(valid_chunks),
            len(deduped),
            len(selected),
            character_count,
            token_estimate,
            truncated,
            duration_ms,
        )

        return ContextResult(
            context_text=context_text,
            sources=sources,
            chunk_count=len(selected),
            character_count=character_count,
            token_estimate=token_estimate,
            truncated=truncated,
        )

    # ── Private helpers ───────────────────────────────────────────────────────

    def _validate_chunks(
        self, chunks: list[RetrievedChunk]
    ) -> list[RetrievedChunk]:
        """
        Validate each chunk and return only structurally valid ones.

        A chunk is valid if it has:
            - A non-empty chunk_id string.
            - A non-empty document_id string.
            - A non-empty content string (at least _MIN_CONTENT_LENGTH chars).
            - A numeric rank >= 1.
            - A numeric score.

        Invalid chunks are skipped and logged.  This never crashes the build.

        Args:
            chunks: Raw list from the ContextRequest.

        Returns:
            List of structurally valid RetrievedChunk objects.
        """
        valid: list[RetrievedChunk] = []
        skipped = 0

        for i, chunk in enumerate(chunks):
            reason = self._validate_chunk(chunk)
            if reason is None:
                valid.append(chunk)
            else:
                skipped += 1
                logger.debug(
                    "ContextBuilder — skipping invalid chunk at index=%d: %s",
                    i, reason,
                )

        if skipped:
            logger.warning(
                "ContextBuilder — skipped %d invalid chunk(s) out of %d total.",
                skipped, len(chunks),
            )

        return valid

    @staticmethod
    def _validate_chunk(chunk: RetrievedChunk) -> Optional[str]:
        """
        Validate a single chunk.  Returns None if valid, reason string if not.
        """
        if not isinstance(chunk, RetrievedChunk):
            return f"expected RetrievedChunk, got {type(chunk).__name__}"
        if not chunk.chunk_id or not isinstance(chunk.chunk_id, str):
            return "chunk_id is empty or not a string"
        if not chunk.document_id or not isinstance(chunk.document_id, str):
            return "document_id is empty or not a string"
        if not chunk.content or len(chunk.content.strip()) < _MIN_CONTENT_LENGTH:
            return "content is empty or whitespace-only"
        if not isinstance(chunk.rank, int) or chunk.rank < 1:
            return f"rank must be an integer >= 1, got {chunk.rank!r}"
        if not isinstance(chunk.score, (int, float)):
            return f"score must be numeric, got {type(chunk.score).__name__}"
        return None

    @staticmethod
    def _deduplicate(
        chunks: list[RetrievedChunk],
    ) -> list[RetrievedChunk]:
        """
        Defensive deduplication: keep the best-ranked occurrence of each chunk_id.

        "Best-ranked" = lowest rank value (rank 1 is better than rank 2).
        If two chunks share the same rank, prefer the one with the higher score.

        This is a second deduplication layer on top of FAISSRetriever's own
        deduplication (Day 71).  It handles the case where multiple vector IDs
        in FAISS map to the same chunk (e.g. from re-indexing).

        Uses a dict for O(n) time complexity, not O(n²).

        Args:
            chunks: Validated chunks, may contain duplicate chunk_ids.

        Returns:
            List with at most one entry per chunk_id, duplicate-free.
        """
        best: dict[str, RetrievedChunk] = {}
        for chunk in chunks:
            existing = best.get(chunk.chunk_id)
            if existing is None:
                best[chunk.chunk_id] = chunk
            else:
                # Keep the one with the lower rank (closer to rank 1 = better)
                # Tie-break: prefer higher score.
                if chunk.rank < existing.rank or (
                    chunk.rank == existing.rank and chunk.score > existing.score
                ):
                    best[chunk.chunk_id] = chunk

        return list(best.values())

    def _apply_budget(
        self,
        chunks: list[RetrievedChunk],
        *,
        max_chunks: int,
        max_characters: int,
        max_tokens: int,
    ) -> tuple[list[RetrievedChunk], bool]:
        """
        Select chunks that fit within all three budget limits.

        Strategy:
            - Iterate chunks in rank order (best first).
            - Add each chunk if it fits within the remaining character and token budget.
            - Stop as soon as max_chunks is reached or a budget is exceeded.
            - If a single chunk is individually too large, truncate its content
              at the character boundary while preserving its source metadata.
            - Mark truncated=True if any chunk was dropped or truncated.

        Args:
            chunks       : Ordered (rank ascending) validated, deduped chunks.
            max_chunks   : Maximum number of chunks to select.
            max_characters: Maximum total character count.
            max_tokens   : Approximate maximum token count (chars // 4).

        Returns:
            (selected_chunks, truncated_flag)
        """
        selected: list[RetrievedChunk] = []
        char_used = 0
        truncated = False

        for chunk in chunks:
            if len(selected) >= max_chunks:
                truncated = True
                break

            content = chunk.content
            content_chars = len(content)
            content_tokens = content_chars // _CHARS_PER_TOKEN_ESTIMATE

            remaining_chars = max_characters - char_used
            remaining_tokens = max_tokens - (char_used // _CHARS_PER_TOKEN_ESTIMATE)

            # Determine effective character limit for this chunk
            effective_char_limit = min(remaining_chars, remaining_tokens * _CHARS_PER_TOKEN_ESTIMATE)

            if effective_char_limit <= 0:
                truncated = True
                break

            if content_chars <= effective_char_limit:
                # Chunk fits entirely — include as-is
                selected.append(chunk)
                char_used += content_chars
            else:
                # Chunk is too large — truncate its content at a safe boundary
                truncated_content = self._safe_truncate(content, effective_char_limit)
                if truncated_content:
                    # Create a truncated copy preserving all source metadata
                    from dataclasses import replace
                    truncated_chunk = replace(chunk, content=truncated_content)
                    selected.append(truncated_chunk)
                    char_used += len(truncated_content)
                truncated = True
                break  # Budget exhausted after truncation

        if len(chunks) > len(selected) and not truncated:
            truncated = True

        return selected, truncated

    @staticmethod
    def _safe_truncate(text: str, max_chars: int) -> str:
        """
        Truncate text at a safe word boundary up to max_chars characters.

        Tries to break at the last whitespace before the limit to avoid
        cutting through a word mid-character.  Falls back to hard truncation
        if no whitespace is found (e.g. very long unbroken tokens).

        Args:
            text      : Original content string.
            max_chars : Maximum character count for the result.

        Returns:
            Truncated string, always <= max_chars characters.
        """
        if max_chars <= 0:
            return ""
        if len(text) <= max_chars:
            return text

        truncated = text[:max_chars]

        # Try to break at the last whitespace
        last_space = truncated.rfind(" ")
        if last_space > max_chars // 2:
            # Only use word boundary if it's in the second half of the budget
            truncated = truncated[:last_space]

        return truncated.rstrip()

    @staticmethod
    def _format_context(
        chunks: list[RetrievedChunk],
        *,
        include_metadata: bool,
    ) -> str:
        """
        Format selected chunks into a deterministic, structured context string.

        Structure:
            <retrieved_context>
            <source rank="1">
            [Document: <name>]
            [Chunk ID: <id>]
            [Relevance Score: <score>]

            <content>
            ...
            </content>
            </source>
            ...
            </retrieved_context>

        The <retrieved_context> wrapper is the explicit data boundary signal
        for the PromptBuilder.  Retrieved text is ALWAYS inside this boundary,
        never promoted to system-instruction level.

        Args:
            chunks           : Selected, ordered, budget-limited chunks.
            include_metadata : Whether to include document/chunk metadata headers.

        Returns:
            Formatted context string.  Empty string if chunks is empty.
        """
        if not chunks:
            return ""

        source_sections: list[str] = []

        for chunk in chunks:
            lines: list[str] = []

            if include_metadata:
                lines.append(f"Document: {chunk.document_name}")
                lines.append(f"Chunk ID: {chunk.chunk_id}")
                lines.append(f"Relevance Score: {chunk.score:.4f}")
                lines.append("")  # blank separator

            lines.append("<content>")
            lines.append(chunk.content)
            lines.append("</content>")

            section_body = "\n".join(lines)
            source_sections.append(
                f'<source rank="{chunk.rank}">\n{section_body}\n</source>'
            )

        body = "\n\n".join(source_sections)
        return f"<retrieved_context>\n{body}\n</retrieved_context>"
