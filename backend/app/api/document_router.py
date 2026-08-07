"""
Document Router — HTTP endpoints for the Document Management module (Day 66 Part A1).

Prefix: /documents
Tags:   Document Management

Endpoints:
    POST   /documents/upload         — Upload a document
    GET    /documents                — List user's documents (paginated)
    GET    /documents/health         — Storage health check
    GET    /documents/metrics        — Upload/download metrics
    GET    /documents/{id}           — Get document metadata
    PATCH  /documents/{id}           — Rename document
    DELETE /documents/{id}           — Soft-delete (archive) document
    GET    /documents/{id}/download  — Stream document for download

Security:
    - Every endpoint requires authentication via get_current_user.
    - Ownership is validated in DocumentService on every document operation.
    - storage_path and checksum are never returned to the client.
    - Download streams the file — the physical path is never exposed.
"""
import logging
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, File, Query, UploadFile, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.dependencies.current_user import get_current_user
from app.models.document import DocumentStatus
from app.models.user import User
from app.schemas.document import (
    DocumentDeleteResponse,
    DocumentDetailResponse,
    DocumentListResponse,
    DocumentMetricsResponse,
    DocumentRenameRequest,
    DocumentUploadResponse,
    DocumentFilterParams,
    ParsedDocumentResponse,
    StorageHealthResponse,
)
from app.services import document_service as service
from app.storage.storage_service import get_storage_metrics, storage_service
from app.storage.storage_health_service import StorageHealthService

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/documents",
    tags=["Document Management"],
)


# ── Upload ────────────────────────────────────────────────────────────────────

@router.post(
    "/upload",
    response_model=DocumentUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a document",
    description=(
        "Upload a PDF, TXT, or Markdown file. "
        "Maximum size: configurable (default 25 MB). "
        "Duplicate uploads for the same user are rejected. "
        "The file is stored securely with a UUID filename."
    ),
)
async def upload_document(
    file: UploadFile = File(
        ...,
        description="Document file (PDF, TXT, or .md). Max 25 MB.",
    ),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DocumentUploadResponse:
    logger.info(
        "POST /documents/upload — user_id=%d filename=%r",
        current_user.id,
        file.filename,
    )
    return await service.upload_document(
        db=db,
        user_id=current_user.id,
        file=file,
        background_tasks=background_tasks,
    )


# ── List ──────────────────────────────────────────────────────────────────────

@router.get(
    "",
    response_model=DocumentListResponse,
    summary="List documents",
    description=(
        "Returns a paginated list of the authenticated user's documents. "
        "Archived documents are excluded by default. "
        "Supports filtering by status and sorting by newest/oldest/name."
    ),
)
def list_documents(
    status_filter: Optional[DocumentStatus] = Query(
        default=None,
        alias="status",
        description="Filter by document status (UPLOADED, PROCESSING, READY, FAILED).",
    ),
    page: int = Query(default=1, ge=1, description="Page number (1-indexed)."),
    page_size: int = Query(default=20, ge=1, le=100, description="Records per page."),
    sort: str = Query(
        default="newest",
        description="Sort order: 'newest', 'oldest', or 'name'.",
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DocumentListResponse:
    filters = DocumentFilterParams(
        status=status_filter,
        page=page,
        page_size=page_size,
        sort=sort,
    )
    return service.list_documents(db=db, user_id=current_user.id, filters=filters)


# ── Health & Metrics (before /{id} to avoid path collision) ──────────────────

@router.get(
    "/health",
    response_model=StorageHealthResponse,
    summary="Storage health check",
    description="Returns the health status of the underlying storage provider.",
)
def storage_health(
    current_user: User = Depends(get_current_user),
) -> StorageHealthResponse:
    health_svc = StorageHealthService(storage_service.provider)
    report = health_svc.check()
    return StorageHealthResponse(
        healthy=report.healthy,
        provider=report.provider,
        directory_exists=report.directory_exists,
        directory_readable=report.directory_readable,
        directory_writable=report.directory_writable,
        disk_free_bytes=report.disk_free_bytes,
        disk_usage_percent=report.disk_usage_percent,
        errors=report.errors,
    )


@router.get(
    "/metrics",
    response_model=DocumentMetricsResponse,
    summary="Document upload/download metrics",
    description="Returns aggregate metrics for document operations.",
)
def document_metrics(
    current_user: User = Depends(get_current_user),
) -> DocumentMetricsResponse:
    doc_m = service.get_document_metrics()
    st_m = get_storage_metrics()

    total_uploads = st_m.get("uploads_total", 0)
    total_bytes = st_m.get("total_bytes_uploaded", 0)
    total_latency = st_m.get("total_upload_latency_ms", 0.0)
    duplicates = doc_m.get("duplicates_rejected", 0)

    avg_size = total_bytes / total_uploads if total_uploads > 0 else None
    avg_latency = total_latency / total_uploads if total_uploads > 0 else None
    dup_rate = duplicates / total_uploads if total_uploads > 0 else None

    return DocumentMetricsResponse(
        uploads_total=doc_m.get("uploads_total", 0),
        uploads_failed=doc_m.get("uploads_failed", 0),
        downloads_total=doc_m.get("downloads_total", 0),
        downloads_failed=st_m.get("downloads_failed", 0),
        deletes_total=doc_m.get("archives_total", 0),
        total_bytes_uploaded=total_bytes,
        average_upload_size_bytes=avg_size,
        average_upload_latency_ms=avg_latency,
        duplicate_rate=dup_rate,
    )


# ── Get single document ───────────────────────────────────────────────────────

@router.get(
    "/{document_id}",
    response_model=DocumentDetailResponse,
    summary="Get document metadata",
    description=(
        "Returns full metadata for a single document. "
        "Only the owning user may access their documents. "
        "Does not return file content — use /download for that."
    ),
)
def get_document(
    document_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DocumentDetailResponse:
    return service.get_document(
        db=db,
        document_id=document_id,
        user_id=current_user.id,
    )


# ── Rename ────────────────────────────────────────────────────────────────────

@router.patch(
    "/{document_id}",
    response_model=DocumentDetailResponse,
    summary="Rename a document",
    description=(
        "Update the display name of a document. "
        "The original filename and stored filename are never modified. "
        "Only the owning user may rename their documents."
    ),
)
def rename_document(
    document_id: str,
    data: DocumentRenameRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DocumentDetailResponse:
    return service.rename_document(
        db=db,
        document_id=document_id,
        user_id=current_user.id,
        data=data,
    )


# ── Delete ────────────────────────────────────────────────────────────────────

@router.delete(
    "/{document_id}",
    response_model=DocumentDeleteResponse,
    summary="Delete a document",
    description=(
        "Soft-deletes a document by setting its status to ARCHIVED. "
        "The physical file is not immediately removed. "
        "Only the owning user may delete their documents."
    ),
)
def delete_document(
    document_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DocumentDeleteResponse:
    return service.delete_document(
        db=db,
        document_id=document_id,
        user_id=current_user.id,
    )


# ── Download ──────────────────────────────────────────────────────────────────

@router.get(
    "/{document_id}/download",
    summary="Download a document",
    description=(
        "Streams the document file for download. "
        "Only the owning user may download their documents. "
        "The physical storage path is never exposed in the response."
    ),
    responses={
        200: {"description": "Streaming file download"},
        403: {"description": "Access denied — document belongs to another user"},
        404: {"description": "Document not found"},
        410: {"description": "Document has been deleted"},
    },
)
async def download_document(
    document_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> StreamingResponse:
    generator, media_type, filename = await service.stream_document(
        db=db,
        document_id=document_id,
        user_id=current_user.id,
    )
    logger.info(
        "GET /documents/%s/download — user_id=%d filename=%r",
        document_id,
        current_user.id,
        filename,
    )
    return StreamingResponse(
        content=generator,
        media_type=media_type,
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "X-Document-ID": document_id,
        },
    )


# ── Parsed Text ────────────────────────────────────────────────────────────────────

@router.get(
    "/{document_id}/parsed",
    response_model=ParsedDocumentResponse,
    summary="Get parsed document text",
    description=(
        "Returns the extracted text content from a parsed document. "
        "Returns 404 if parsing has not completed yet. "
        "Only the owning user may access their documents."
    ),
    responses={
        200: {"description": "Parsed text with metadata"},
        403: {"description": "Access denied — document belongs to another user"},
        404: {"description": "Document not found or not yet parsed"},
        410: {"description": "Document has been deleted"},
    },
)
def get_parsed_document(
    document_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ParsedDocumentResponse:
    from app.repositories.parsed_document_repository import (
        get_parsed_document as get_parsed,
    )
    from fastapi import HTTPException

    # Verify ownership via existing service helper
    service.get_document(db=db, document_id=document_id, user_id=current_user.id)

    parsed = get_parsed(db, document_id)
    if not parsed:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document has not been parsed yet. Please try again shortly.",
        )

    return ParsedDocumentResponse(
        document_id=parsed.document_id,
        status=parsed.status,
        text_content=parsed.text_content or "",
        char_count=len(parsed.text_content or ""),
        created_at=parsed.created_at,
        updated_at=parsed.updated_at,
    )


# ── Retry Parsing ─────────────────────────────────────────────────────────────────

@router.post(
    "/{document_id}/retry",
    response_model=DocumentDetailResponse,
    summary="Retry parsing a failed document",
    description=(
        "Re-enqueues text extraction for a document whose parsing failed. "
        "Only the owning user may trigger a retry."
    ),
)
def retry_document_parsing(
    document_id: str,
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DocumentDetailResponse:
    from app.repositories.parsed_document_repository import get_parsed_document as get_parsed
    from app.services.document_parsing_service import DocumentParsingService
    from app.core.database import SessionLocal

    doc = service.get_document(db=db, document_id=document_id, user_id=current_user.id)

    # Delete existing parsed_document record if present so process_document can re-run
    parsed = get_parsed(db, document_id)
    if parsed:
        db.delete(parsed)
        db.commit()

    def _run_retry() -> None:
        retry_db = SessionLocal()
        try:
            DocumentParsingService.process_document(retry_db, document_id)
        except Exception as exc:
            logger.error("Retry parsing failed for document %s: %s", document_id, exc)
        finally:
            retry_db.close()

    background_tasks.add_task(_run_retry)
    logger.info("POST /documents/%s/retry — enqueued by user_id=%d", document_id, current_user.id)

    # Return refreshed detail
    return service.get_document(db=db, document_id=document_id, user_id=current_user.id)


# ── Chunk Management Endpoints (Day 68) ──────────────────────────────────────────

@router.get(
    "/{document_id}/chunks",
    summary="Get document chunks",
    description="Returns a paginated list of intelligent text chunks generated for a document.",
)
def get_document_chunks(
    document_id: str,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=100, ge=1, le=500),
    status_filter: Optional[str] = Query(default=None, alias="status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from app.services.chunk_service import ChunkService

    return ChunkService.get_chunks(
        db,
        document_id=document_id,
        user_id=current_user.id,
        page=page,
        page_size=page_size,
        status_filter=status_filter,
    )


@router.get(
    "/{document_id}/chunks/metadata",
    summary="Get chunk metadata",
    description="Returns aggregate chunk statistics (totals, average tokens, strategy) for a document.",
)
def get_chunk_metadata(
    document_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from app.services.chunk_service import ChunkService

    return ChunkService.get_chunk_metadata(
        db,
        document_id=document_id,
        user_id=current_user.id,
    )


@router.post(
    "/{document_id}/rechunk",
    summary="Re-chunk a document",
    description="Archives existing chunks and re-enqueues intelligent chunk generation.",
)
def rechunk_document(
    document_id: str,
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from app.jobs.chunk_generation_job import run_rechunk_job

    # Verify ownership
    service.get_document(db=db, document_id=document_id, user_id=current_user.id)

    background_tasks.add_task(
        run_rechunk_job,
        document_id=document_id,
        user_id=current_user.id,
    )
    logger.info("POST /documents/%s/rechunk — enqueued by user_id=%d", document_id, current_user.id)
    return {"message": "Rechunking job enqueued successfully.", "document_id": document_id}


