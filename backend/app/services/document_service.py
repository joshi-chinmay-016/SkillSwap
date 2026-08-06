"""
DocumentService — business logic for the Document Management module (Day 66 Part A1).

Responsibilities:
    - File type validation (MIME + extension)
    - File size validation
    - Checksum generation
    - Per-user duplicate detection
    - Upload orchestration (storage → metadata → database)
    - Ownership enforcement on every operation
    - Rename (display_name update)
    - Soft-delete (archive)
    - Document retrieval
    - Logging and metrics

Business logic belongs here.
    Repository  → persistence only.
    StorageService → file IO only.
    Router      → HTTP concerns only.

Designed for zero architectural changes when:
    - Day 67 adds parsing (parser calls DocumentService.get_document())
    - Day 66 A2 already introduced StorageService abstraction
    - Future: cloud storage swap requires only provider config change
"""
from __future__ import annotations

import logging
import uuid
from typing import AsyncGenerator

from fastapi import BackgroundTasks, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.document import Document, DocumentStatus
from app.repositories import document_repository as doc_repo
from app.schemas.document import (
    DocumentDeleteResponse,
    DocumentDetailResponse,
    DocumentFilterParams,
    DocumentListResponse,
    DocumentListItem,
    DocumentRenameRequest,
    DocumentUploadResponse,
)
from app.storage.storage_service import StorageService, storage_service as _default_storage
from app.utils.checksum import calculate_sha256_stream
from app.utils.file_validation import (
    build_display_name,
    generate_stored_filename,
    sanitize_filename,
    validate_file_extension,
    validate_file_size,
    validate_mime_type,
)

logger = logging.getLogger(__name__)

# ── Metrics ───────────────────────────────────────────────────────────────────
_metrics: dict = {
    "uploads_total": 0,
    "uploads_failed": 0,
    "duplicates_rejected": 0,
    "renames_total": 0,
    "archives_total": 0,
    "downloads_total": 0,
    "validation_failures": 0,
    "total_bytes_uploaded": 0,
}


def get_document_metrics() -> dict:
    """Return a snapshot of document service metrics."""
    return dict(_metrics)


# ── Internal helpers ──────────────────────────────────────────────────────────

def _get_document_or_404(db: Session, document_id: str) -> Document:
    """
    Return a Document by ID or raise HTTP 404.

    Does NOT validate ownership — call _assert_ownership() after this.
    """
    doc = doc_repo.get_document(db, document_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document '{document_id}' not found.",
        )
    return doc


def _assert_ownership(document: Document, user_id: int) -> None:
    """
    Raise HTTP 403 if the document does not belong to ``user_id``.

    This is a hard security check — do not remove or weaken it.
    """
    if document.user_id != user_id:
        logger.warning(
            "Ownership violation: user_id=%d attempted to access document owned by user_id=%d (doc_id=%s)",
            user_id,
            document.user_id,
            document.id,
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this document.",
        )


def _assert_not_archived(document: Document) -> None:
    """Raise HTTP 410 if the document has been archived / soft-deleted."""
    if document.status == DocumentStatus.ARCHIVED.value:
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="This document has been deleted.",
        )


def _get_owned_active_document(
    db: Session, document_id: str, user_id: int
) -> Document:
    """
    Convenience: fetch a document, verify ownership, verify not archived.
    Used by rename, delete, download, get-by-id.
    """
    doc = _get_document_or_404(db, document_id)
    _assert_ownership(doc, user_id)
    _assert_not_archived(doc)
    return doc


# ── Public service functions ──────────────────────────────────────────────────

async def upload_document(
    db: Session,
    user_id: int,
    file: UploadFile,
    background_tasks: BackgroundTasks | None = None,
    _storage: StorageService | None = None,
) -> DocumentUploadResponse:
    """
    Full upload orchestration flow:

        1. Validate authentication (caller's responsibility — user_id is trusted).
        2. Validate file type (extension + MIME).
        3. Validate file size.
        4. Read file bytes and calculate SHA-256 checksum.
        5. Check for per-user duplicate (same checksum).
        6. Generate document UUID.
        7. Save file via StorageService.
        8. Persist metadata to database.
        9. Return upload response.

    Args:
        db:       SQLAlchemy Session.
        user_id:  Authenticated user's ID.
        file:     FastAPI UploadFile from the multipart request.
        _storage: Optional StorageService override (for testing).

    Returns:
        :class:`DocumentUploadResponse`.

    Raises:
        HTTPException 415: Unsupported file type.
        HTTPException 413: File too large.
        HTTPException 409: Duplicate upload for this user.
        HTTPException 503: Storage unavailable.
        HTTPException 500: Unexpected failure.
    """
    storage = _storage or _default_storage

    logger.info(
        "upload_document — user_id=%d filename=%r content_type=%r",
        user_id,
        file.filename,
        file.content_type,
    )

    # ── Step 1: Sanitize filename ────────────────────────────────────────────
    safe_filename = sanitize_filename(file.filename or "upload")

    # ── Step 2: Validate extension ───────────────────────────────────────────
    try:
        extension = validate_file_extension(safe_filename)
    except HTTPException:
        _metrics["validation_failures"] += 1
        logger.warning(
            "Upload rejected — unsupported extension: user_id=%d filename=%r",
            user_id,
            safe_filename,
        )
        raise

    # ── Step 3: Validate MIME type ───────────────────────────────────────────
    content_type = file.content_type or "application/octet-stream"
    try:
        mime_type = validate_mime_type(content_type, extension)
    except HTTPException:
        _metrics["validation_failures"] += 1
        logger.warning(
            "Upload rejected — MIME mismatch: user_id=%d filename=%r content_type=%r",
            user_id,
            safe_filename,
            content_type,
        )
        raise

    # ── Step 4: Read bytes + checksum ────────────────────────────────────────
    checksum, file_bytes = await calculate_sha256_stream(file)
    file_size = len(file_bytes)

    # ── Step 5: Validate size ────────────────────────────────────────────────
    try:
        validate_file_size(file_size, max_bytes=settings.MAX_FILE_SIZE)
    except HTTPException:
        _metrics["validation_failures"] += 1
        logger.warning(
            "Upload rejected — file too large: user_id=%d size=%d limit=%d",
            user_id,
            file_size,
            settings.MAX_FILE_SIZE,
        )
        raise

    logger.debug(
        "upload_document validation passed — user_id=%d size=%d checksum=%s",
        user_id,
        file_size,
        checksum,
    )

    # ── Step 6: Duplicate detection ──────────────────────────────────────────
    policy = getattr(settings, "DUPLICATE_UPLOAD_POLICY", "REJECT").upper()
    existing = doc_repo.find_by_checksum(db, checksum=checksum, user_id=user_id)
    if existing:
        _metrics["duplicates_rejected"] += 1
        if policy == "REJECT":
            logger.info(
                "Duplicate upload rejected — user_id=%d checksum=%s existing_id=%s",
                user_id,
                checksum,
                existing.id,
            )
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    f"You have already uploaded this file as '{existing.display_name}' "
                    f"(ID: {existing.id}). Duplicate uploads are not allowed."
                ),
            )
        # Future: REUSE or ALLOW policies can be implemented here.

    # ── Step 7: Generate IDs + paths ─────────────────────────────────────────
    document_id = str(uuid.uuid4())
    stored_filename = generate_stored_filename(document_id, extension)
    display_name = build_display_name(safe_filename)

    # ── Step 8: Persist file to storage ──────────────────────────────────────
    logger.info(
        "upload_document — saving file: user_id=%d document_id=%s",
        user_id,
        document_id,
    )
    storage_meta = storage.save_file(
        file_data=file_bytes,
        user_id=user_id,
        document_id=document_id,
        extension=extension,
    )

    # ── Step 9: Persist metadata to database ─────────────────────────────────
    try:
        doc = doc_repo.create_document(
            db,
            id=document_id,
            user_id=user_id,
            original_filename=safe_filename,
            stored_filename=stored_filename,
            display_name=display_name,
            file_extension=extension,
            mime_type=mime_type,
            file_size=storage_meta.size,
            storage_path=storage_meta.storage_path,
            checksum=storage_meta.checksum,
            status=DocumentStatus.UPLOADED.value,
        )
        db.commit()
        db.refresh(doc)
    except Exception as exc:
        db.rollback()
        # Best-effort cleanup: remove the orphaned file
        try:
            storage.delete_file(storage_meta.storage_path)
            logger.info(
                "upload_document — orphan file cleaned up after DB failure: %s",
                storage_meta.storage_path,
            )
        except Exception as cleanup_exc:  # noqa: BLE001
            logger.error(
                "upload_document — cleanup failed for orphan file: %s — %s",
                storage_meta.storage_path,
                cleanup_exc,
            )
        _metrics["uploads_failed"] += 1
        logger.error("upload_document — database commit failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save document metadata. The file has been removed.",
        )

    _metrics["uploads_total"] += 1
    _metrics["total_bytes_uploaded"] += storage_meta.size

    logger.info(
        "upload_document complete — document_id=%s user_id=%d display_name=%r size=%d",
        document_id,
        user_id,
        display_name,
        storage_meta.size,
    )

    # ── Trigger async parsing (Day 67) ────────────────────────────────────
    if background_tasks is not None:
        from app.services.document_parsing_service import DocumentParsingService

        def _run_parsing() -> None:
            """Execute parsing in a background thread with a fresh DB session."""
            from app.core.database import SessionLocal

            parsing_db = SessionLocal()
            try:
                DocumentParsingService.process_document(parsing_db, document_id)
            except Exception as parse_exc:  # noqa: BLE001
                logger.error(
                    "Background parsing failed for document %s: %s",
                    document_id,
                    parse_exc,
                )
            finally:
                parsing_db.close()

        background_tasks.add_task(_run_parsing)
        logger.info(
            "upload_document — parsing enqueued for document_id=%s",
            document_id,
        )

    return DocumentUploadResponse.model_validate(doc)


def get_document(
    db: Session, document_id: str, user_id: int
) -> DocumentDetailResponse:
    """
    Return full metadata for a single owned document.

    Args:
        db:          SQLAlchemy Session.
        document_id: UUID string.
        user_id:     Authenticated user's ID.

    Returns:
        :class:`DocumentDetailResponse`.

    Raises:
        HTTPException 404: Document not found.
        HTTPException 403: Document belongs to another user.
        HTTPException 410: Document has been archived.
    """
    doc = _get_owned_active_document(db, document_id, user_id)
    return DocumentDetailResponse.model_validate(doc)


def list_documents(
    db: Session,
    user_id: int,
    filters: DocumentFilterParams,
) -> DocumentListResponse:
    """
    Return a paginated list of documents for the authenticated user.

    Args:
        db:      SQLAlchemy Session.
        user_id: Authenticated user's ID.
        filters: Query parameters (page, page_size, status, sort).

    Returns:
        :class:`DocumentListResponse` with pagination metadata.
    """
    status_value = filters.status.value if filters.status else None
    documents, total = doc_repo.list_documents(
        db,
        user_id=user_id,
        page=filters.page,
        page_size=filters.page_size,
        status=status_value,
        sort=filters.sort,
    )

    items = [DocumentListItem.model_validate(d) for d in documents]
    has_next = (filters.page * filters.page_size) < total
    has_previous = filters.page > 1

    return DocumentListResponse(
        documents=items,
        total=total,
        page=filters.page,
        page_size=filters.page_size,
        has_next=has_next,
        has_previous=has_previous,
    )


def rename_document(
    db: Session,
    document_id: str,
    user_id: int,
    data: DocumentRenameRequest,
) -> DocumentDetailResponse:
    """
    Update the display_name of a document.

    Does NOT modify the stored filename or any other field.

    Args:
        db:          SQLAlchemy Session.
        document_id: UUID string.
        user_id:     Authenticated user's ID.
        data:        :class:`DocumentRenameRequest` with new display_name.

    Returns:
        Updated :class:`DocumentDetailResponse`.
    """
    doc = _get_owned_active_document(db, document_id, user_id)
    old_name = doc.display_name

    doc = doc_repo.update_document(db, doc, display_name=data.display_name)
    db.commit()
    db.refresh(doc)

    _metrics["renames_total"] += 1
    logger.info(
        "rename_document — document_id=%s user_id=%d '%s' → '%s'",
        document_id,
        user_id,
        old_name,
        data.display_name,
    )

    return DocumentDetailResponse.model_validate(doc)


def delete_document(
    db: Session,
    document_id: str,
    user_id: int,
    _storage: StorageService | None = None,
) -> DocumentDeleteResponse:
    """
    Soft-delete (archive) a document.

    Sets status → ARCHIVED and records deleted_at.
    Physical file is NOT removed yet — future cleanup job handles this.

    Args:
        db:          SQLAlchemy Session.
        document_id: UUID string.
        user_id:     Authenticated user's ID.
        _storage:    Optional StorageService override (for testing).

    Returns:
        :class:`DocumentDeleteResponse`.
    """
    doc = _get_owned_active_document(db, document_id, user_id)

    doc = doc_repo.archive_document(db, doc)
    db.commit()

    _metrics["archives_total"] += 1
    logger.info(
        "delete_document (soft) — document_id=%s user_id=%d display_name=%r",
        document_id,
        user_id,
        doc.display_name,
    )

    return DocumentDeleteResponse(
        id=document_id,
        status=DocumentStatus.ARCHIVED.value,
        message=f"Document '{doc.display_name}' has been deleted.",
    )


async def stream_document(
    db: Session,
    document_id: str,
    user_id: int,
    _storage: StorageService | None = None,
) -> tuple[AsyncGenerator[bytes, None], str, str]:
    """
    Validate ownership and return a streaming generator for download.

    Args:
        db:          SQLAlchemy Session.
        document_id: UUID string.
        user_id:     Authenticated user's ID.
        _storage:    Optional StorageService override (for testing).

    Returns:
        Tuple of (async_generator, media_type, filename).

    Raises:
        HTTPException 404: Document not found.
        HTTPException 403: Ownership violation.
        HTTPException 410: Document is archived.
    """
    storage = _storage or _default_storage
    doc = _get_owned_active_document(db, document_id, user_id)

    _metrics["downloads_total"] += 1
    logger.info(
        "stream_document — document_id=%s user_id=%d storage_path=%s",
        document_id,
        user_id,
        doc.storage_path,
    )

    generator = storage.stream_file(doc.storage_path)
    return generator, doc.mime_type, doc.original_filename
