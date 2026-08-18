"""
AnswerValidator — Day 74 Part A1.

Validates the LLM-generated answer before it is returned to the caller.

The AnswerValidator is the final gate in the grounded-answer pipeline:

    LLM Provider
         │
         ▼
    raw_answer (str)
         │
         ▼
    AnswerValidator.validate()
         │
         ├── non-empty check
         ├── length guard (RAG_MAX_ANSWER_LENGTH)
         ├── source integrity: every source.chunk_id ∈ retrieved_chunk_ids
         └── document-level source deduplication (keep best-ranked per doc)
         │
         ▼
    AnswerValidationResult
         ├── valid: bool
         ├── grounded: bool          (True iff validation passed AND context present)
         ├── deduplicated_sources    (one ContextSource per unique document_id)
         ├── invalid_source_ids      (chunk_ids that were NOT in retrieved set)
         └── failure_reason          (human-readable, None on success)

Design constraints (enforced):
    - Does NOT call the LLM.
    - Does NOT access FAISS or any vector store.
    - Does NOT modify the database.
    - Does NOT log raw answer text or source content (private user data).
    - Does NOT invent confidence values.
    - Does NOT introduce arbitrary score thresholds.

Source fabrication protection:
    The LLM CANNOT invent source identifiers because AnswerValidator operates
    on the backend-controlled ContextSource list from ContextBuilder — not on
    any LLM-generated source text.  The server is always authoritative for
    which sources were retrieved.

Deduplication:
    When multiple chunks come from the same document, the API should present
    one source card per document (best-ranked chunk selected).  Chunk identity
    is preserved internally for traceability; only the API-facing list is
    collapsed.

Grounded definition:
    grounded = True iff:
        - has_context is True  (retrieved context was non-empty)
        - valid is True        (validation passed)
        - no invalid source IDs detected

    grounded = False iff:
        - insufficient_context (no relevant knowledge — controlled refusal)
        - answer is empty or oversized
        - any source ID is not in the retrieved set (fabrication detected)
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Optional

from app.rag.context_models import ContextSource

logger = logging.getLogger(__name__)

# Minimum answer length for a grounded response (avoids empty-string grounded=True)
_MIN_ANSWER_LENGTH = 1


@dataclass
class AnswerValidationResult:
    """
    Structured result from AnswerValidator.validate().

    Fields:
        valid                : True if all validation checks passed.
        grounded             : True if the answer is grounded (valid + has context).
        deduplicated_sources : Document-level deduplicated source list for the API.
                               One ContextSource per unique document_id; best-ranked
                               chunk selected where multiple chunks share a document.
        invalid_source_ids   : chunk_ids that were not present in the retrieved set.
                               Empty on valid responses.
        failure_reason       : Human-readable failure description.  None on success.
    """

    valid: bool
    grounded: bool
    deduplicated_sources: list[ContextSource] = field(default_factory=list)
    invalid_source_ids: list[str] = field(default_factory=list)
    failure_reason: Optional[str] = None


class AnswerValidator:
    """
    Validates LLM-generated answers before returning them to callers.

    Usage::

        validator = AnswerValidator(max_answer_length=8192)
        result = validator.validate(
            answer=raw_answer,
            sources=context_sources,          # backend-controlled ContextSource list
            retrieved_chunk_ids={"c1", "c2"}, # from RetrievalResponse.results
            has_context=True,
        )
        if not result.valid:
            raise InvalidGenerationResponseError(result.failure_reason)

    Args:
        max_answer_length : Maximum character count for a valid answer.
    """

    def __init__(self, *, max_answer_length: int) -> None:
        self._max_answer_length = max_answer_length

    # ── Public interface ──────────────────────────────────────────────────────

    def validate(
        self,
        *,
        answer: str,
        sources: list[ContextSource],
        retrieved_chunk_ids: set[str],
        has_context: bool,
    ) -> AnswerValidationResult:
        """
        Validate the LLM-generated answer and return structured results.

        Steps:
            1. Non-empty check.
            2. Answer length guard.
            3. Source integrity: verify every source.chunk_id ∈ retrieved_chunk_ids.
            4. Document-level deduplication of sources.
            5. Compute grounded flag.

        Args:
            answer              : Raw LLM-generated answer string (already stripped).
            sources             : Backend-controlled ContextSource list from ContextBuilder.
            retrieved_chunk_ids : Set of chunk_id values from RetrievalResponse.results.
            has_context         : True if the context window was non-empty.

        Returns:
            AnswerValidationResult — always returned, never raises.
        """
        # ── Step 1: Non-empty check ───────────────────────────────────────────
        if not answer or len(answer.strip()) < _MIN_ANSWER_LENGTH:
            logger.warning(
                "AnswerValidator — validation failed: answer is empty."
            )
            return AnswerValidationResult(
                valid=False,
                grounded=False,
                failure_reason="Generated answer is empty.",
            )

        # ── Step 2: Answer length guard ───────────────────────────────────────
        if len(answer) > self._max_answer_length:
            logger.warning(
                "AnswerValidator — validation failed: answer length=%d exceeds max=%d.",
                len(answer),
                self._max_answer_length,
            )
            return AnswerValidationResult(
                valid=False,
                grounded=False,
                failure_reason=(
                    f"Generated answer length ({len(answer)} chars) exceeds "
                    f"maximum allowed ({self._max_answer_length} chars)."
                ),
            )

        # ── Step 3: Source integrity check ────────────────────────────────────
        valid_sources, invalid_chunk_ids = self._validate_sources(
            sources, retrieved_chunk_ids
        )

        if invalid_chunk_ids:
            logger.warning(
                "AnswerValidator — invalid source chunk_ids detected: count=%d. "
                "Removing from response. retrieved_set_size=%d",
                len(invalid_chunk_ids),
                len(retrieved_chunk_ids),
            )
            # Continue with only valid sources — do NOT expose invalid IDs to caller.

        # ── Step 4: Document-level deduplication ──────────────────────────────
        deduplicated = self._deduplicate_by_document(valid_sources)

        # ── Step 5: Compute grounded flag ─────────────────────────────────────
        # grounded = True iff:
        #   - answer is valid (non-empty, within length limit)
        #   - context was present (has_context=True)
        #   - no invalid source IDs detected (source integrity intact)
        grounded = has_context and len(invalid_chunk_ids) == 0

        logger.info(
            "AnswerValidator — validation complete: valid=True grounded=%s "
            "total_sources=%d valid_sources=%d invalid_sources=%d deduped_sources=%d",
            grounded,
            len(sources),
            len(valid_sources),
            len(invalid_chunk_ids),
            len(deduplicated),
        )

        return AnswerValidationResult(
            valid=True,
            grounded=grounded,
            deduplicated_sources=deduplicated,
            invalid_source_ids=list(invalid_chunk_ids),
        )

    # ── Private helpers ───────────────────────────────────────────────────────

    @staticmethod
    def _validate_sources(
        sources: list[ContextSource],
        retrieved_chunk_ids: set[str],
    ) -> tuple[list[ContextSource], set[str]]:
        """
        Verify that every source in the list originated from the retrieved set.

        Args:
            sources             : Backend-controlled ContextSource list.
            retrieved_chunk_ids : Set of valid chunk_id values from the Retriever.

        Returns:
            (valid_sources, invalid_chunk_ids) tuple.
            - valid_sources: only sources whose chunk_id ∈ retrieved_chunk_ids.
            - invalid_chunk_ids: chunk_ids NOT in the retrieved set.
        """
        if not retrieved_chunk_ids:
            # No retrieved chunks → all sources are invalid (empty context case).
            # This should not occur in practice (ContextBuilder produces no sources
            # when retrieved_chunks is empty), but guard defensively.
            invalid = {src.chunk_id for src in sources if src.chunk_id}
            return [], invalid

        valid: list[ContextSource] = []
        invalid: set[str] = set()

        for src in sources:
            if src.chunk_id in retrieved_chunk_ids:
                valid.append(src)
            else:
                invalid.add(src.chunk_id)

        return valid, invalid

    @staticmethod
    def _deduplicate_by_document(
        sources: list[ContextSource],
    ) -> list[ContextSource]:
        """
        Collapse sources to one entry per unique document_id.

        When multiple chunks come from the same document, keep the best-ranked
        chunk (lowest rank value; tie-break on higher score).

        The frontend shows one source card per document.  Internal chunk
        identity is preserved in the non-deduplicated list held by RAGService.

        Preserves the relative document ordering (by best rank of each group).

        Args:
            sources : Validated ContextSource list.

        Returns:
            Deduplicated list, one ContextSource per unique document_id.
        """
        best: dict[str, ContextSource] = {}

        for src in sources:
            existing = best.get(src.document_id)
            if existing is None:
                best[src.document_id] = src
            else:
                # Lower rank = better (rank 1 is best)
                if src.rank < existing.rank or (
                    src.rank == existing.rank and src.score > existing.score
                ):
                    best[src.document_id] = src

        # Re-order by rank to preserve deterministic ordering
        return sorted(best.values(), key=lambda s: (s.rank, s.document_id))
