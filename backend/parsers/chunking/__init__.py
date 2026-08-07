"""
Chunking sub-package — Day 68 Part A1.

Strategy hierarchy:
    ChunkStrategy (abstract)
    └── RecursiveChunkStrategy   (default)

    Future:
    ├── ParagraphChunkStrategy
    ├── HeadingAwareChunkStrategy
    ├── MarkdownAwareChunkStrategy
    ├── CodeAwareChunkStrategy
    ├── SemanticChunkStrategy
    └── TokenBasedChunkStrategy
"""
from parsers.chunking.chunk_strategy import ChunkStrategy
from parsers.chunking.recursive_chunk_strategy import RecursiveChunkStrategy
from parsers.chunking.chunk_factory import ChunkFactory

__all__ = [
    "ChunkStrategy",
    "RecursiveChunkStrategy",
    "ChunkFactory",
]
