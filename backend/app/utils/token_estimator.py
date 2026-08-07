"""
token_estimator — Lightweight token count approximation (Day 68 Part A1).

Purpose:
    Provide a simple, dependency-free approximation of the number of tokens
    a given text will consume when processed by an embedding model.

Current implementation:
    tokens ≈ characters / 4

    This is a widely-used heuristic for English text with modern BPE tokenizers
    (GPT-2, GPT-3, GPT-4, Gemini).  For dense technical text or non-English
    content the real count may differ by ±25%.

Future:
    When an embedding model is selected (Day 69+), this module can be swapped
    for a real tokenizer (tiktoken, HuggingFace tokenizers, sentencepiece)
    without changing any calling code.
"""
from __future__ import annotations


_CHARS_PER_TOKEN: float = 4.0  # configurable heuristic


def estimate_tokens(text: str) -> int:
    """
    Return an approximate token count for the given text.

    Args:
        text: Any plain-text string.

    Returns:
        Non-negative integer estimate.  0 for empty/None input.

    Example:
        >>> estimate_tokens("Hello, world!")
        3
    """
    if not text:
        return 0
    return max(1, round(len(text) / _CHARS_PER_TOKEN))


def estimate_tokens_for_chunks(texts: list[str]) -> list[int]:
    """
    Batch token estimation for a list of text chunks.

    Args:
        texts: List of chunk text strings.

    Returns:
        List of estimated token counts, same length as input.
    """
    return [estimate_tokens(t) for t in texts]
