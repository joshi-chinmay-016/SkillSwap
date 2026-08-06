"""
Checksum utilities — Day 66.

Purpose:
    - Duplicate detection: same user uploading identical content.
    - Integrity validation: verify stored file has not been corrupted.
    - Future caching: parser can skip re-processing if checksum unchanged.

Algorithm: SHA-256 (collision-resistant, standard for file integrity).

Usage:
    from app.utils.checksum import calculate_sha256, calculate_sha256_stream

    # From bytes already in memory (small files):
    digest = calculate_sha256(file_bytes)

    # From a file-like object / UploadFile (streaming, memory-efficient):
    digest = await calculate_sha256_stream(upload_file)
"""
import hashlib
from typing import AsyncIterator


# Chunk size used when hashing streams: 64 KB
_CHUNK_SIZE = 65_536


def calculate_sha256(data: bytes) -> str:
    """
    Calculate SHA-256 hex digest of ``data``.

    Args:
        data: Raw bytes to hash.

    Returns:
        64-character lowercase hexadecimal string.
    """
    return hashlib.sha256(data).hexdigest()


def calculate_sha256_incremental(chunks: list[bytes]) -> str:
    """
    Calculate SHA-256 by feeding multiple byte chunks incrementally.

    Useful when a file has already been read in pieces and reassembled
    in a list, avoiding a second full read.

    Args:
        chunks: Ordered list of byte chunks.

    Returns:
        64-character lowercase hexadecimal string.
    """
    hasher = hashlib.sha256()
    for chunk in chunks:
        hasher.update(chunk)
    return hasher.hexdigest()


async def calculate_sha256_stream(upload_file) -> tuple[str, bytes]:
    """
    Read a FastAPI ``UploadFile`` fully, calculate SHA-256, and return
    both the digest and the raw bytes.

    The file pointer is reset to 0 after reading so downstream code
    can re-read the content for storage.

    Args:
        upload_file: A ``fastapi.UploadFile`` instance.

    Returns:
        Tuple of (hex_digest: str, raw_bytes: bytes).
    """
    hasher = hashlib.sha256()
    chunks: list[bytes] = []

    await upload_file.seek(0)
    while True:
        chunk = await upload_file.read(_CHUNK_SIZE)
        if not chunk:
            break
        hasher.update(chunk)
        chunks.append(chunk)

    # Reset pointer so storage layer can re-read.
    await upload_file.seek(0)

    raw_bytes = b"".join(chunks)
    return hasher.hexdigest(), raw_bytes
