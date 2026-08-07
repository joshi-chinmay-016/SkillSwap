"""
ChunkStrategy — Abstract interface for all chunking strategies (Day 68 Part A1).

Every chunking strategy MUST implement three methods:

    supports(document_type: str) -> bool
        Return True when this strategy is suitable for the given document type.
        (e.g. "pdf", "md", "txt")

    chunk(text: str, **kwargs) -> list[ChunkData]
        Produce an ordered list of ChunkData objects from the supplied text.
        Must never modify the original text.

    validate(chunks: list[ChunkData]) -> list[str]
        Return a (possibly empty) list of human-readable validation error messages.
        An empty list means the chunk set is valid.

Design principles:
    - Each strategy is independently replaceable.
    - Strategies depend only on plain text input — no DB or HTTP calls.
    - The ChunkData intermediate object is the canonical hand-off unit.
"""
from __future__ import annotations

import abc
import dataclasses
from typing import Optional


@dataclasses.dataclass
class ChunkData:
    """
    Immutable intermediate object produced by any ChunkStrategy.

    Carries everything needed to construct a Chunk DB record without
    touching the database.  Services convert ChunkData → Chunk model.

    Fields
    ------
    chunk_index       : Zero-based position of this chunk in the document.
    chunk_text        : The actual text content of the chunk.
    start_offset      : Character position (inclusive) where the chunk begins.
    end_offset        : Character position (exclusive) where the chunk ends.
    estimated_tokens  : Approximate token count (chars / 4, rounded).
    chunk_size        : Maximum chunk size configuration used (chars).
    overlap_size      : Overlap configuration used (chars).
    page_start        : First page this chunk spans (if available).
    page_end          : Last page this chunk spans (if available).
    section           : Section/heading label this chunk falls under.
    strategy          : Name of the strategy that produced this chunk.
    strategy_version  : Semantic version of the strategy.
    """

    chunk_index: int
    chunk_text: str
    start_offset: int
    end_offset: int
    estimated_tokens: int
    chunk_size: int
    overlap_size: int
    page_start: Optional[int] = None
    page_end: Optional[int] = None
    section: Optional[str] = None
    strategy: str = "recursive"
    strategy_version: str = "1.0.0"

    def __post_init__(self) -> None:
        if self.chunk_index < 0:
            raise ValueError("chunk_index must be >= 0")
        if self.start_offset < 0:
            raise ValueError("start_offset must be >= 0")
        if self.end_offset < self.start_offset:
            raise ValueError("end_offset must be >= start_offset")
        if self.estimated_tokens < 0:
            raise ValueError("estimated_tokens must be >= 0")

    @property
    def char_count(self) -> int:
        """Number of characters in this chunk (derived from offsets)."""
        return self.end_offset - self.start_offset


class ChunkStrategy(abc.ABC):
    """
    Abstract base class for all text chunking strategies.

    Concrete implementations must be stateless — every public method
    receives all required inputs as arguments.
    """

    # ── Identity ──────────────────────────────────────────────────────────────

    @property
    @abc.abstractmethod
    def name(self) -> str:
        """Unique lowercase name for this strategy (e.g. 'recursive')."""
        raise NotImplementedError

    @property
    @abc.abstractmethod
    def version(self) -> str:
        """Semantic version string (e.g. '1.0.0')."""
        raise NotImplementedError

    # ── Public Interface ──────────────────────────────────────────────────────

    @abc.abstractmethod
    def supports(self, document_type: str) -> bool:
        """Return True if this strategy handles the given document type.

        Args:
            document_type: Lowercase file extension without dot ('pdf', 'md', 'txt').

        Returns:
            bool indicating support.
        """
        raise NotImplementedError

    @abc.abstractmethod
    def chunk(
        self,
        text: str,
        *,
        chunk_size: int = 800,
        chunk_overlap: int = 150,
        document_type: str = "txt",
    ) -> list[ChunkData]:
        """Transform plain text into an ordered list of ChunkData objects.

        This method must:
            - Never modify the input text.
            - Preserve paragraph boundaries where possible.
            - Preserve sentence boundaries where possible.
            - Keep headings with their associated content where possible.
            - Generate non-overlapping primary text with configurable overlap halos.
            - Assign correct chunk_index (0, 1, 2, …) in reading order.
            - Track accurate start_offset / end_offset into the original text.

        Args:
            text         : Raw extracted text from a ParsedDocument.
            chunk_size   : Target maximum character count per chunk.
            chunk_overlap: Number of characters to repeat at chunk boundaries.
            document_type: Lowercase file extension for format-specific logic.

        Returns:
            Ordered list of ChunkData. Empty if text is empty.
        """
        raise NotImplementedError

    @abc.abstractmethod
    def validate(self, chunks: list[ChunkData]) -> list[str]:
        """Validate the produced chunk list and return any error messages.

        Args:
            chunks: Output of :meth:`chunk`.

        Returns:
            List of human-readable error strings.
            An empty list means the chunk set is valid.
        """
        raise NotImplementedError
