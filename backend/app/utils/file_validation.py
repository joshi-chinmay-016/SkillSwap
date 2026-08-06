"""
File Validation Utilities — Day 66.

Responsibilities:
    - MIME type validation (do not trust extension alone)
    - Extension whitelist enforcement
    - File size guard
    - Safe filename generation (prevents path traversal attacks)

Supported file types (Part 6):
    PDF   — application/pdf
    TXT   — text/plain
    MD    — text/markdown, text/x-markdown, text/plain (with .md extension)

Rejected:
    DOCX, ZIP, EXE, images, videos, scripts, etc.

Security notes:
    - A file named ``fake.pdf.exe`` will fail MIME sniffing even if the
      extension is stripped to ``.exe``.
    - A file named ``../../etc/passwd.pdf`` has its path components stripped
      by ``sanitize_filename`` — only the basename is kept.
    - UUID-based stored filenames eliminate filename-based attacks entirely.
"""
import re
import uuid
from pathlib import Path

from fastapi import HTTPException, status


# ── Allowlists ────────────────────────────────────────────────────────────────

ALLOWED_EXTENSIONS: frozenset[str] = frozenset({"pdf", "txt", "md"})

# Map extension → accepted MIME types (one extension can have multiple valid MIMEs)
ALLOWED_MIME_BY_EXTENSION: dict[str, frozenset[str]] = {
    "pdf": frozenset({"application/pdf"}),
    "txt": frozenset({"text/plain"}),
    "md": frozenset({"text/markdown", "text/x-markdown", "text/plain"}),
}

# Reverse map: MIME → accepted extensions (used when extension is unrecognised)
ALLOWED_MIME_TYPES: frozenset[str] = frozenset(
    mime
    for mimes in ALLOWED_MIME_BY_EXTENSION.values()
    for mime in mimes
)

# Human-readable names for error messages
ALLOWED_TYPE_LABEL = "PDF, TXT, or Markdown (.md)"

# Default max upload: 25 MB (overridden by settings.MAX_FILE_SIZE)
DEFAULT_MAX_BYTES: int = 25 * 1024 * 1024


# ── Public API ────────────────────────────────────────────────────────────────

def get_file_extension(filename: str) -> str:
    """
    Extract the lowercase extension from a filename, without the dot.

    Examples:
        "Algorithms Notes.pdf" → "pdf"
        "readme.MD"            → "md"
        "noextension"          → ""

    Args:
        filename: Raw filename string.

    Returns:
        Lowercase extension without leading dot, or empty string.
    """
    suffix = Path(filename).suffix
    return suffix.lstrip(".").lower() if suffix else ""


def validate_file_extension(filename: str) -> str:
    """
    Ensure the file extension is in the allowed whitelist.

    Args:
        filename: Original upload filename.

    Returns:
        Validated lowercase extension string.

    Raises:
        HTTPException 415: Extension not supported.
    """
    ext = get_file_extension(filename)
    if not ext or ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=(
                f"File extension '.{ext}' is not supported. "
                f"Accepted types: {ALLOWED_TYPE_LABEL}."
            ),
        )
    return ext


def validate_mime_type(content_type: str, extension: str) -> str:
    """
    Validate that the uploaded MIME type is consistent with the extension.

    This prevents MIME spoofing attacks such as renaming an EXE to .pdf.
    Both the MIME type AND the extension must be in the allowlist.

    Args:
        content_type: MIME type reported by the HTTP client (e.g. ``application/pdf``).
        extension:    Already-validated lowercase extension (e.g. ``pdf``).

    Returns:
        The normalised MIME type string.

    Raises:
        HTTPException 415: MIME type not allowed or inconsistent with extension.
    """
    # Strip parameters (e.g. "text/plain; charset=utf-8" → "text/plain")
    mime = content_type.split(";")[0].strip().lower()

    if mime not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=(
                f"MIME type '{mime}' is not supported. "
                f"Accepted types: {ALLOWED_TYPE_LABEL}."
            ),
        )

    allowed_mimes_for_ext = ALLOWED_MIME_BY_EXTENSION.get(extension, frozenset())
    if mime not in allowed_mimes_for_ext:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=(
                f"MIME type '{mime}' is inconsistent with extension '.{extension}'. "
                "Possible MIME spoofing attempt rejected."
            ),
        )

    return mime


def validate_file_size(size_bytes: int, max_bytes: int = DEFAULT_MAX_BYTES) -> None:
    """
    Reject files that exceed the configured maximum.

    Args:
        size_bytes: Actual file size in bytes.
        max_bytes:  Maximum allowed size in bytes (default 25 MB).

    Raises:
        HTTPException 413: File exceeds the size limit.
    """
    if size_bytes > max_bytes:
        max_mb = max_bytes / (1024 * 1024)
        actual_mb = size_bytes / (1024 * 1024)
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=(
                f"File size {actual_mb:.2f} MB exceeds the maximum allowed "
                f"{max_mb:.0f} MB."
            ),
        )


def sanitize_filename(filename: str) -> str:
    """
    Strip directory components and dangerous characters from a filename.

    Defends against:
        - Path traversal: ``../../etc/passwd`` → ``passwd``
        - Null bytes and control characters
        - Leading dots that hide files on Unix systems

    Args:
        filename: Raw original filename from the upload.

    Returns:
        Safe basename only (no path components).
    """
    # Keep only the basename — kills all path traversal attempts
    safe = Path(filename).name

    # Remove null bytes and control characters
    safe = re.sub(r"[\x00-\x1f\x7f]", "", safe)

    # Collapse multiple dots to prevent "file.pdf.exe" confusion
    # (extension validation will still reject non-allowed extensions)
    safe = safe.strip()

    # Fallback for empty result
    if not safe:
        safe = "upload"

    return safe


def generate_stored_filename(document_id: str, extension: str) -> str:
    """
    Generate a UUID-based storage filename.

    The document_id (UUID) is used directly so the stored filename
    and the database ID are the same value.

    Args:
        document_id: UUID string for the document record.
        extension:   Validated lowercase extension (without dot).

    Returns:
        Filename string: ``{document_id}.{extension}``

    Example:
        "e43dd4bb-acde-46ab-beef-123456789abc.pdf"
    """
    return f"{document_id}.{extension}"


def build_display_name(original_filename: str) -> str:
    """
    Derive a human-readable display name from the original filename.

    Strips the file extension and returns the stem.

    Examples:
        "Algorithms Notes.pdf" → "Algorithms Notes"
        "readme.md"            → "readme"

    Args:
        original_filename: Raw filename from the upload.

    Returns:
        Display name string (may be renamed later via PATCH /documents/{id}).
    """
    return Path(sanitize_filename(original_filename)).stem or "Untitled"
