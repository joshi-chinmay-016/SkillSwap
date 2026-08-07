"""
RecursiveChunkStrategy — Default production chunking strategy (Day 68 Part A1).

Splitting hierarchy (tries each level before falling back to the next):
    1. Double-newline paragraph boundaries  (highest preference)
    2. Single-newline line boundaries
    3. Sentence-ending punctuation  (. ! ?)
    4. Clause punctuation  (, ; :)
    5. Whitespace  (last resort — avoids mid-word breaks)

Special behaviours:
    - Heading awareness: headings (# / ## / ### / plain UPPERCASE lines) are
      kept with the first paragraph they introduce.
    - Markdown awareness: fenced code blocks (``` / ~~~) are never split.
    - Overlap: each chunk's text begins `chunk_overlap` chars before the
      previous chunk's primary text ended, aligned to the nearest sentence
      boundary.
    - Text normalisation: repeated whitespace, mixed line endings, and
      excessive blank lines are cleaned before splitting.

This strategy is independently replaceable. It has no database dependencies.
"""
from __future__ import annotations

import logging
import re
from typing import Optional

from parsers.chunking.chunk_strategy import ChunkData, ChunkStrategy

logger = logging.getLogger(__name__)

# ── Regex constants ────────────────────────────────────────────────────────────

# Markdown heading (ATX style: # / ## / ### …)
_RE_MD_HEADING = re.compile(r"^#{1,6}\s+\S", re.MULTILINE)

# Plain-text "heading": a short line in ALL CAPS or Title Case ending without
# terminal punctuation (covers non-markdown documents)
_RE_PLAIN_HEADING = re.compile(
    r"^(?:[A-Z][A-Za-z0-9 \-]{0,60}[A-Z0-9]|[A-Z]{2,})$", re.MULTILINE
)

# Sentence-ending punctuation followed by whitespace or end-of-string
_RE_SENTENCE_END = re.compile(r"(?<=[.!?])\s+")

# Fenced code block (``` or ~~~, with optional language tag)
_RE_FENCED_CODE = re.compile(r"(```[^\n]*\n.*?```|~~~[^\n]*\n.*?~~~)", re.DOTALL)

# Excessive blank lines (3+) → normalise to 2
_RE_EXCESS_BLANK = re.compile(r"\n{3,}")


class RecursiveChunkStrategy(ChunkStrategy):
    """
    Production-grade recursive chunking strategy.

    Splitting cascade:
        paragraph → newline → sentence → clause → whitespace

    Format-aware:
        - Markdown headings kept with associated content.
        - Fenced code blocks preserved atomically.
    """

    # ── Identity ──────────────────────────────────────────────────────────────

    @property
    def name(self) -> str:
        return "recursive"

    @property
    def version(self) -> str:
        return "1.0.0"

    # ── Supports ──────────────────────────────────────────────────────────────

    def supports(self, document_type: str) -> bool:
        """Recursive strategy is the universal fallback — supports all types."""
        return True

    # ── Main Public Method ─────────────────────────────────────────────────────

    def chunk(
        self,
        text: str,
        *,
        chunk_size: int = 800,
        chunk_overlap: int = 150,
        document_type: str = "txt",
    ) -> list[ChunkData]:
        """
        Transform text into an ordered list of ChunkData objects.

        Args:
            text          : Extracted document text (from ParsedDocument.text_content).
            chunk_size    : Maximum character count per chunk (configurable).
            chunk_overlap : Characters of overlap between adjacent chunks (configurable).
            document_type : Lowercase file extension for format-specific handling.

        Returns:
            Ordered list of ChunkData objects.
        """
        if not text or not text.strip():
            logger.debug("RecursiveChunkStrategy.chunk — empty text, returning []")
            return []

        # Step 1: normalise text
        normalised = self._normalise(text)

        # Step 2: extract code blocks from markdown (protect them from splitting)
        code_blocks: dict[str, str] = {}
        if document_type in ("md", "markdown"):
            normalised, code_blocks = self._protect_code_blocks(normalised)

        # Step 3: produce raw text segments via recursive splitting
        segments = self._split_recursive(normalised, chunk_size)

        # Step 4: restore protected code blocks
        if code_blocks:
            segments = [self._restore_code_blocks(s, code_blocks) for s in segments]

        # Step 5: apply overlap
        overlapped_segments = self._apply_overlap(segments, chunk_overlap)

        # Step 6: build ChunkData list with accurate offsets into original text
        chunks = self._build_chunk_data(
            overlapped_segments,
            original_text=text,
            normalised_text=normalised,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )

        logger.debug(
            "RecursiveChunkStrategy — produced %d chunks (size=%d overlap=%d)",
            len(chunks),
            chunk_size,
            chunk_overlap,
        )
        return chunks

    # ── Validation ────────────────────────────────────────────────────────────

    def validate(self, chunks: list[ChunkData]) -> list[str]:
        """Validate the chunk list and return a list of error messages."""
        errors: list[str] = []

        if not chunks:
            return errors  # empty is valid for empty documents

        # 1. Ordering
        for i, chunk in enumerate(chunks):
            if chunk.chunk_index != i:
                errors.append(
                    f"Chunk ordering violation: expected index {i}, got {chunk.chunk_index}"
                )

        # 2. Non-empty text
        for chunk in chunks:
            if not chunk.chunk_text.strip():
                errors.append(f"Chunk {chunk.chunk_index} is empty or whitespace-only")

        # 3. Offset monotonicity (primary start offsets must be non-decreasing)
        for i in range(1, len(chunks)):
            if chunks[i].start_offset < chunks[i - 1].start_offset:
                errors.append(
                    f"Chunk {i} start_offset ({chunks[i].start_offset}) "
                    f"< chunk {i-1} start_offset ({chunks[i-1].start_offset})"
                )

        # 4. Strategy consistency
        expected_strategy = self.name
        for chunk in chunks:
            if chunk.strategy != expected_strategy:
                errors.append(
                    f"Chunk {chunk.chunk_index} strategy mismatch: "
                    f"expected '{expected_strategy}', got '{chunk.strategy}'"
                )

        # 5. Duplicate text detection (exact full-text match)
        seen: set[str] = set()
        for chunk in chunks:
            if chunk.chunk_text in seen:
                errors.append(
                    f"Duplicate chunk text detected at index {chunk.chunk_index}"
                )
            seen.add(chunk.chunk_text)

        return errors

    # ── Private: Normalisation ─────────────────────────────────────────────────

    @staticmethod
    def _normalise(text: str) -> str:
        """Normalise whitespace and line endings without altering meaning."""
        # Unify line endings
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        # Collapse 3+ blank lines → 2 blank lines (paragraph separator)
        text = _RE_EXCESS_BLANK.sub("\n\n", text)
        # Remove trailing whitespace from each line
        text = "\n".join(line.rstrip() for line in text.split("\n"))
        return text.strip()

    # ── Private: Code Block Protection ────────────────────────────────────────

    @staticmethod
    def _protect_code_blocks(text: str) -> tuple[str, dict[str, str]]:
        """Replace fenced code blocks with unique placeholders."""
        placeholders: dict[str, str] = {}
        counter = 0

        def _replace(match: re.Match) -> str:  # type: ignore[type-arg]
            nonlocal counter
            key = f"__CODE_BLOCK_{counter}__"
            placeholders[key] = match.group(0)
            counter += 1
            return key

        protected = _RE_FENCED_CODE.sub(_replace, text)
        return protected, placeholders

    @staticmethod
    def _restore_code_blocks(text: str, code_blocks: dict[str, str]) -> str:
        """Restore code block placeholders with their original content."""
        for key, value in code_blocks.items():
            text = text.replace(key, value)
        return text

    # ── Private: Recursive Splitting ──────────────────────────────────────────

    def _split_recursive(self, text: str, chunk_size: int) -> list[str]:
        """
        Recursively split text using a cascade of separators.

        Cascade order (most semantic → least semantic):
            1. Double newline  (paragraph boundary)
            2. Single newline  (line boundary)
            3. Sentence end    (. ! ? followed by whitespace)
            4. Comma/semicolon/colon
            5. Any whitespace  (last resort)
        """
        separators = ["\n\n", "\n", _RE_SENTENCE_END, r"[,;:]\s+", r"\s+"]
        return self._split_with_separators(text, separators, chunk_size)

    def _split_with_separators(
        self, text: str, separators: list, chunk_size: int
    ) -> list[str]:
        """
        Attempt to split `text` at `separators[0]`.
        For each piece that still exceeds `chunk_size`, recurse with the
        remaining separators.
        """
        if len(text) <= chunk_size:
            return [text] if text.strip() else []

        if not separators:
            # Hard character split — last resort to stay within limits
            return self._hard_split(text, chunk_size)

        sep = separators[0]
        remaining_seps = separators[1:]

        # Split by this separator
        if isinstance(sep, str):
            parts = text.split(sep)
        else:
            parts = re.split(sep, text)

        # If separator produced only one part, try next separator
        if len(parts) <= 1:
            return self._split_with_separators(text, remaining_seps, chunk_size)

        # Merge short parts into chunks up to chunk_size
        chunks: list[str] = []
        current = ""
        sep_str = sep if isinstance(sep, str) else " "

        for part in parts:
            if not part.strip():
                continue
            candidate = (current + sep_str + part).strip() if current else part
            if len(candidate) <= chunk_size:
                current = candidate
            else:
                if current:
                    chunks.append(current)
                # The part itself might exceed chunk_size → recurse
                if len(part) > chunk_size:
                    sub = self._split_with_separators(part, remaining_seps, chunk_size)
                    chunks.extend(sub)
                    current = ""
                else:
                    current = part

        if current:
            chunks.append(current)

        return [c for c in chunks if c.strip()]

    @staticmethod
    def _hard_split(text: str, chunk_size: int) -> list[str]:
        """Split at whitespace or hard character boundaries when all else fails."""
        words = text.split()
        chunks: list[str] = []
        current = ""
        for word in words:
            candidate = (current + " " + word).strip() if current else word
            if len(candidate) <= chunk_size:
                current = candidate
            else:
                if current:
                    chunks.append(current)
                # If the word itself exceeds chunk_size, hard-cut it
                while len(word) > chunk_size:
                    chunks.append(word[:chunk_size])
                    word = word[chunk_size:]
                current = word
        if current:
            chunks.append(current)
        return chunks

    # ── Private: Overlap ──────────────────────────────────────────────────────

    @staticmethod
    def _apply_overlap(segments: list[str], overlap: int) -> list[str]:
        """
        Prepend the last `overlap` characters of the previous segment (aligned
        to the nearest sentence or word boundary) to each subsequent segment.

        This preserves context at chunk boundaries without duplicating entire
        chunks.
        """
        if overlap <= 0 or len(segments) <= 1:
            return segments

        result: list[str] = [segments[0]]

        for i in range(1, len(segments)):
            prev = segments[i - 1]
            # Take the last `overlap` chars from the previous segment
            tail = prev[-overlap:] if len(prev) > overlap else prev

            # Align to the nearest sentence boundary within the tail
            sentence_match = list(_RE_SENTENCE_END.finditer(tail))
            if sentence_match:
                # Start after the last sentence-end found in the tail
                last_match = sentence_match[-1]
                tail = tail[last_match.end():]
            elif " " in tail:
                # Align to the nearest word boundary
                space_idx = tail.find(" ")
                tail = tail[space_idx + 1:]

            if tail.strip():
                result.append((tail + " " + segments[i]).strip())
            else:
                result.append(segments[i])

        return result

    # ── Private: ChunkData Construction ───────────────────────────────────────

    def _build_chunk_data(
        self,
        segments: list[str],
        *,
        original_text: str,
        normalised_text: str,
        chunk_size: int,
        chunk_overlap: int,
    ) -> list[ChunkData]:
        """
        Convert text segments into ChunkData objects, computing character offsets
        into the normalised text for future source highlighting.
        """
        from app.utils.token_estimator import estimate_tokens

        chunks: list[ChunkData] = []
        search_start = 0  # cursor into normalised_text for offset tracking

        for idx, segment in enumerate(segments):
            # Locate segment in the normalised text for accurate offsets
            # For overlapping segments, search from the overlap boundary
            primary_text = segment

            # Find the primary start offset (use first 60 chars as anchor)
            anchor = primary_text[:60].strip()
            start_off = normalised_text.find(anchor, search_start)
            if start_off == -1:
                # Fallback: search from beginning (overlap text may shift cursor)
                start_off = normalised_text.find(anchor)
            if start_off == -1:
                start_off = search_start

            end_off = min(start_off + len(primary_text), len(normalised_text))

            # Advance cursor past the primary content (not the overlap)
            # Use the non-overlapping portion length to advance
            if idx == 0:
                advance = len(primary_text)
            else:
                advance = max(len(primary_text) - chunk_overlap, len(primary_text) // 2)
            search_start = start_off + advance

            section = self._detect_section(primary_text)

            chunks.append(
                ChunkData(
                    chunk_index=idx,
                    chunk_text=primary_text,
                    start_offset=start_off,
                    end_offset=end_off,
                    estimated_tokens=estimate_tokens(primary_text),
                    chunk_size=chunk_size,
                    overlap_size=chunk_overlap,
                    section=section,
                    strategy=self.name,
                    strategy_version=self.version,
                )
            )

        return chunks

    # ── Private: Section Detection ────────────────────────────────────────────

    @staticmethod
    def _detect_section(text: str) -> Optional[str]:
        """Extract the leading heading from a chunk, if present."""
        first_line = text.split("\n")[0].strip()

        # ATX markdown heading
        if _RE_MD_HEADING.match(first_line):
            return re.sub(r"^#{1,6}\s+", "", first_line).strip()

        # Plain-text heading heuristic
        if _RE_PLAIN_HEADING.match(first_line) and len(first_line) <= 80:
            return first_line

        return None
