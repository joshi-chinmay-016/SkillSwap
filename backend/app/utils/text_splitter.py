"""
text_splitter — Pure-function text processing pipeline (Day 68 Part A1).

Each stage is independently callable and testable.

Pipeline:
    raw text
        ↓ normalize()
        ↓ split_paragraphs()
        ↓ split_by_sentences()
        ↓ apply_overlap_to_segments()
        ↓ list of text segments

No database dependencies.  No strategy coupling.
"""
from __future__ import annotations

import re


# ── Regex constants ────────────────────────────────────────────────────────────

_RE_CRLF = re.compile(r"\r\n|\r")
_RE_EXCESS_BLANK_LINES = re.compile(r"\n{3,}")
_RE_TRAILING_SPACE = re.compile(r"[ \t]+$", re.MULTILINE)
_RE_REPEATED_SPACE = re.compile(r"[ \t]{2,}")
_RE_SENTENCE_BOUNDARY = re.compile(r"(?<=[.!?])\s+")
_RE_WORD_BOUNDARY = re.compile(r"\s+")


# ── Stage 1: Normalize ─────────────────────────────────────────────────────────

def normalize(text: str) -> str:
    """
    Normalise line endings, repeated whitespace, and excessive blank lines.

    Does NOT alter the actual semantic content of the document.

    Args:
        text: Raw extracted text.

    Returns:
        Cleaned text string.
    """
    if not text:
        return ""

    # Unify line endings
    text = _RE_CRLF.sub("\n", text)

    # Remove trailing whitespace from each line
    text = _RE_TRAILING_SPACE.sub("", text)

    # Collapse 3+ consecutive blank lines to exactly 2 (paragraph separator)
    text = _RE_EXCESS_BLANK_LINES.sub("\n\n", text)

    # Collapse repeated spaces/tabs within a line to single space
    lines = []
    for line in text.split("\n"):
        lines.append(_RE_REPEATED_SPACE.sub(" ", line))
    text = "\n".join(lines)

    return text.strip()


# ── Stage 2: Split into paragraphs ────────────────────────────────────────────

def split_paragraphs(text: str) -> list[str]:
    """
    Split text at paragraph boundaries (double newlines).

    Args:
        text: Normalised text from :func:`normalize`.

    Returns:
        List of non-empty paragraph strings.
    """
    if not text:
        return []
    paragraphs = text.split("\n\n")
    return [p.strip() for p in paragraphs if p.strip()]


# ── Stage 3: Split paragraph by sentences ────────────────────────────────────

def split_by_sentences(text: str) -> list[str]:
    """
    Split text at sentence boundaries (. ! ? followed by whitespace).

    Preserves sentence integrity — never splits in the middle of a sentence.

    Args:
        text: A paragraph or any text block.

    Returns:
        List of sentence strings.
    """
    if not text:
        return []
    parts = _RE_SENTENCE_BOUNDARY.split(text)
    return [p.strip() for p in parts if p.strip()]


# ── Stage 4: Merge segments into chunks of target size ────────────────────────

def merge_into_chunks(
    segments: list[str],
    chunk_size: int,
    separator: str = " ",
) -> list[str]:
    """
    Greedily merge segments into chunks that do not exceed `chunk_size` chars.

    Args:
        segments  : List of text segments (sentences or paragraphs).
        chunk_size: Maximum character count per chunk.
        separator : String used to join merged segments.

    Returns:
        List of merged chunk strings.
    """
    if not segments:
        return []

    chunks: list[str] = []
    current = ""

    for seg in segments:
        if not seg:
            continue
        candidate = (current + separator + seg).strip() if current else seg
        if len(candidate) <= chunk_size:
            current = candidate
        else:
            if current:
                chunks.append(current)
            # Segment itself may exceed chunk_size — hard split it
            if len(seg) > chunk_size:
                hard = hard_split(seg, chunk_size)
                chunks.extend(hard[:-1])
                current = hard[-1] if hard else ""
            else:
                current = seg

    if current:
        chunks.append(current)

    return chunks


# ── Stage 5: Apply overlap ────────────────────────────────────────────────────

def apply_overlap_to_segments(
    segments: list[str],
    overlap: int,
) -> list[str]:
    """
    Prepend the last `overlap` characters of the previous segment to each
    subsequent segment, aligned to the nearest sentence or word boundary.

    Args:
        segments: Primary text segments (output of :func:`merge_into_chunks`).
        overlap : Number of characters to repeat at boundaries.

    Returns:
        Segments with overlap halos applied.
    """
    if overlap <= 0 or len(segments) <= 1:
        return list(segments)

    result: list[str] = [segments[0]]

    for i in range(1, len(segments)):
        prev = segments[i - 1]
        tail = prev[-overlap:] if len(prev) > overlap else prev

        # Align to sentence boundary
        sentence_parts = _RE_SENTENCE_BOUNDARY.split(tail)
        if len(sentence_parts) > 1:
            tail = sentence_parts[-1].strip()
        elif " " in tail:
            # Align to word boundary
            first_space = tail.find(" ")
            tail = tail[first_space + 1:].strip()

        if tail:
            result.append((tail + " " + segments[i]).strip())
        else:
            result.append(segments[i])

    return result


# ── Utility: Hard character split ─────────────────────────────────────────────

def hard_split(text: str, chunk_size: int) -> list[str]:
    """
    Split text into segments of at most `chunk_size` characters, aligned to
    word boundaries where possible.

    Args:
        text      : Text to split.
        chunk_size: Maximum character count per segment.

    Returns:
        List of text segments.
    """
    if len(text) <= chunk_size:
        return [text] if text else []

    words = _RE_WORD_BOUNDARY.split(text)
    chunks: list[str] = []
    current = ""

    for word in words:
        candidate = (current + " " + word).strip() if current else word
        if len(candidate) <= chunk_size:
            current = candidate
        else:
            if current:
                chunks.append(current)
            # Word itself exceeds chunk_size — hard character cut
            while len(word) > chunk_size:
                chunks.append(word[:chunk_size])
                word = word[chunk_size:]
            current = word

    if current:
        chunks.append(current)

    return chunks


# ── Composite pipeline ────────────────────────────────────────────────────────

def run_pipeline(
    text: str,
    chunk_size: int = 800,
    chunk_overlap: int = 150,
) -> list[str]:
    """
    Execute the full text splitting pipeline end-to-end.

    This function is used as the backbone of RecursiveChunkStrategy but
    can be called independently for testing or alternative pipelines.

    Pipeline:
        normalize → split_paragraphs → (split_by_sentences per paragraph)
        → merge_into_chunks → apply_overlap_to_segments

    Args:
        text         : Raw extracted text.
        chunk_size   : Maximum character count per output chunk.
        chunk_overlap: Overlap character count between adjacent chunks.

    Returns:
        Final list of chunk text strings.
    """
    text = normalize(text)
    if not text:
        return []

    paragraphs = split_paragraphs(text)

    # Expand paragraphs that exceed chunk_size into sentence-level segments
    sentence_segments: list[str] = []
    for para in paragraphs:
        if len(para) <= chunk_size:
            sentence_segments.append(para)
        else:
            sentence_segments.extend(split_by_sentences(para))

    # Merge sentence segments into chunks
    chunks = merge_into_chunks(sentence_segments, chunk_size, separator="\n\n")

    # Apply overlap
    chunks = apply_overlap_to_segments(chunks, chunk_overlap)

    return chunks
