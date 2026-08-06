"""
DocumentRepository — database persistence for Document records (Day 66 Part A1).

Responsibilities: database queries ONLY.
    - No business logic.
    - No authorization / ownership checks.
    - No file IO.
    - No validation.

All ownership validation and business rules live in DocumentService.

Caller (DocumentService) is responsible for committing transactions.
Repository functions call db.flush() after writes so that auto-generated
values (e.g. uploaded_at) are available without a full commit.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import List, Optional, Tuple

from sqlalchemy import asc, desc, func
from sqlalchemy.orm import Session

from app.models.document import Document, DocumentStatus

logger = logging.getLogger(__name__)


# ── Write Operations ──────────────────────────────────────────────────────────

def create_document(
    db: Session,
    *,
    id: str,
    user_id: int,
    original_filename: str,
    stored_filename: str,
    display_name: str,
    file_extension: str,
    mime_type: str,
    file_size: int,
    storage_path: str,
    checksum: str,
    status: str = DocumentStatus.UPLOADED.value,
) -> Document:
    """
    Persist a new Document record.  Caller must commit.

    Args:
        db:                SQLAlchemy Session.
        id:                Pre-generated UUID string for the document.
        user_id:           Owner's user ID.
        original_filename: Raw filename from the upload.
        stored_filename:   UUID-based filename on disk.
        display_name:      Human-readable name (stem of original_filename).
        file_extension:    Lowercase extension without dot.
        mime_type:         Validated MIME type string.
        file_size:         File size in bytes.
        storage_path:      Provider-relative path.
        checksum:          SHA-256 hex digest.
        status:            Initial status (default: UPLOADED).

    Returns:
        Persisted :class:`Document` instance (flushed, not yet committed).
    """
    doc = Document(
        id=id,
        user_id=user_id,
        original_filename=original_filename,
        stored_filename=stored_filename,
        display_name=display_name,
        file_extension=file_extension,
        mime_type=mime_type,
        file_size=file_size,
        storage_path=storage_path,
        checksum=checksum,
        status=status,
    )
    db.add(doc)
    db.flush()
    logger.debug("DocumentRepository.create_document — id=%s user_id=%d", id, user_id)
    return doc


def update_document(
    db: Session,
    document: Document,
    **kwargs,
) -> Document:
    """
    Apply arbitrary field updates to a Document.  Caller must commit.

    Accepted kwargs: display_name, status, updated_at.
    (Other fields are immutable after creation.)

    Args:
        db:       SQLAlchemy Session.
        document: The :class:`Document` instance to update.
        **kwargs: Field name → new value.

    Returns:
        Updated :class:`Document` instance (flushed).
    """
    for field_name, value in kwargs.items():
        setattr(document, field_name, value)
    db.flush()
    return document


def archive_document(db: Session, document: Document) -> Document:
    """
    Soft-delete: set status to ARCHIVED and record deleted_at.  Caller must commit.

    Args:
        db:       SQLAlchemy Session.
        document: The :class:`Document` instance to archive.

    Returns:
        Archived :class:`Document` instance (flushed).
    """
    document.status = DocumentStatus.ARCHIVED.value
    document.deleted_at = datetime.now(timezone.utc)
    db.flush()
    logger.debug(
        "DocumentRepository.archive_document — id=%s user_id=%d",
        document.id,
        document.user_id,
    )
    return document


def delete_document(db: Session, document: Document) -> None:
    """
    Hard-delete the Document record.  Caller must commit.

    Physical file deletion is handled separately by StorageService.

    Args:
        db:       SQLAlchemy Session.
        document: The :class:`Document` instance to delete.
    """
    db.delete(document)
    db.flush()
    logger.debug(
        "DocumentRepository.delete_document — id=%s user_id=%d",
        document.id,
        document.user_id,
    )


# ── Read Operations ───────────────────────────────────────────────────────────

def get_document(db: Session, document_id: str) -> Optional[Document]:
    """
    Return a Document by primary key, or None.

    Args:
        db:          SQLAlchemy Session.
        document_id: UUID string.

    Returns:
        :class:`Document` or None.
    """
    return (
        db.query(Document)
        .filter(Document.id == document_id)
        .first()
    )


def get_user_document(
    db: Session,
    document_id: str,
    user_id: int,
) -> Optional[Document]:
    """
    Return a Document only if it belongs to ``user_id``.

    Used for ownership-validated lookups in the service layer.

    Args:
        db:          SQLAlchemy Session.
        document_id: UUID string.
        user_id:     Expected owner ID.

    Returns:
        :class:`Document` or None.
    """
    return (
        db.query(Document)
        .filter(
            Document.id == document_id,
            Document.user_id == user_id,
        )
        .first()
    )


def list_documents(
    db: Session,
    user_id: int,
    *,
    page: int = 1,
    page_size: int = 20,
    status: Optional[str] = None,
    sort: str = "newest",
    include_archived: bool = False,
) -> Tuple[List[Document], int]:
    """
    Return a paginated list of documents for a user with optional filters.

    Args:
        db:               SQLAlchemy Session.
        user_id:          Owner's user ID.
        page:             1-indexed page number.
        page_size:        Records per page.
        status:           Filter by DocumentStatus value (optional).
        sort:             'newest' | 'oldest' | 'name'.
        include_archived: If False (default), ARCHIVED documents are excluded.

    Returns:
        Tuple of (documents: List[Document], total_count: int).
    """
    query = db.query(Document).filter(Document.user_id == user_id)

    if not include_archived:
        query = query.filter(Document.status != DocumentStatus.ARCHIVED.value)
        query = query.filter(Document.deleted_at.is_(None))

    if status:
        query = query.filter(Document.status == status.upper())

    # ── Sorting ────────────────────────────────────────────────────────────
    if sort == "oldest":
        query = query.order_by(asc(Document.uploaded_at))
    elif sort == "name":
        query = query.order_by(asc(func.lower(Document.display_name)))
    else:  # newest (default)
        query = query.order_by(desc(Document.uploaded_at))

    total = query.count()
    documents = (
        query
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return documents, total


def find_by_checksum(
    db: Session,
    checksum: str,
    user_id: int,
) -> Optional[Document]:
    """
    Find an active (non-archived) document by SHA-256 checksum for a specific user.

    Used for duplicate detection before persisting a new upload.

    Args:
        db:       SQLAlchemy Session.
        checksum: SHA-256 hex digest to search for.
        user_id:  Scope the search to this user only.

    Returns:
        Matching :class:`Document` or None.
    """
    return (
        db.query(Document)
        .filter(
            Document.user_id == user_id,
            Document.checksum == checksum,
            Document.status != DocumentStatus.ARCHIVED.value,
            Document.deleted_at.is_(None),
        )
        .first()
    )


def find_by_filename(
    db: Session,
    original_filename: str,
    user_id: int,
) -> Optional[Document]:
    """
    Find an active document by exact original filename for a specific user.

    Used as a secondary duplicate hint (checksum is the primary check).

    Args:
        db:                SQLAlchemy Session.
        original_filename: Exact filename string.
        user_id:           Scope the search to this user.

    Returns:
        Matching :class:`Document` or None.
    """
    return (
        db.query(Document)
        .filter(
            Document.user_id == user_id,
            Document.original_filename == original_filename,
            Document.status != DocumentStatus.ARCHIVED.value,
            Document.deleted_at.is_(None),
        )
        .first()
    )


def count_user_documents(db: Session, user_id: int) -> int:
    """
    Return the total count of active documents for a user.

    Args:
        db:      SQLAlchemy Session.
        user_id: Owner's user ID.

    Returns:
        Integer count.
    """
    return (
        db.query(Document)
        .filter(
            Document.user_id == user_id,
            Document.status != DocumentStatus.ARCHIVED.value,
            Document.deleted_at.is_(None),
        )
        .count()
    )
