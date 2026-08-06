"""
DocumentParsingService — orchestrates text extraction from uploaded documents (Day 67).

Workflow:
    1. Fetch the Document record.
    2. Mark Document.status → PROCESSING.
    3. Retrieve raw file bytes from StorageService.
    4. Parse according to file extension via :class:`ParserManager`.
    5. Store the extracted text in a ``ParsedDocument`` record.
    6. Update Document.status → READY (or FAILED on error).

This service is intentionally synchronous.  Callers (e.g. the upload endpoint)
may run it in a background task via FastAPI's ``BackgroundTasks`` if desired.
"""
from __future__ import annotations

import logging
from typing import Optional

from sqlalchemy.orm import Session

from app.models.document import Document, DocumentStatus
from app.models.parsed_document import ParsedDocumentStatus
from app.repositories.parsed_document_repository import (
    create_parsed_document,
    get_parsed_document,
    update_parsed_document_status,
)
from app.storage.storage_service import storage_service as _storage_service
from parsers.parser_manager import ParserManager

logger = logging.getLogger(__name__)


class DocumentParsingService:
    """Service responsible for extracting text from an uploaded document."""

    @staticmethod
    def _set_document_status(db: Session, document: Document, status: str) -> None:
        document.status = status
        db.flush()

    @classmethod
    def process_document(cls, db: Session, document_id: str) -> None:
        """Parse a document and persist the extracted text.

        This method is intended to be called after a successful upload.
        It runs synchronously; callers can execute it in a background task.
        """
        # Step 1: fetch Document
        document: Optional[Document] = (
            db.query(Document).filter(Document.id == document_id).first()
        )
        if not document:
            logger.error("DocumentParsingService — document not found: %s", document_id)
            raise ValueError(f"Document {document_id} not found")

        # Guard: skip if already parsed
        existing = get_parsed_document(db, document_id)
        if existing:
            logger.info(
                "DocumentParsingService — already parsed, skipping: %s", document_id
            )
            return

        # Step 2: mark as processing
        cls._set_document_status(db, document, DocumentStatus.PROCESSING.value)
        db.commit()

        try:
            # Step 3: retrieve raw bytes from storage
            file_bytes = _storage_service.get_file(document.storage_path)

            # Step 4: parse using appropriate parser
            extracted_text = ParserManager.parse_document(
                file_bytes, document.file_extension
            )

            # Step 5: create ParsedDocument entry
            create_parsed_document(
                db,
                document_id=document.id,
                text_content=extracted_text,
                status=ParsedDocumentStatus.READY.value,
            )

            # Step 6: mark document as ready
            cls._set_document_status(db, document, DocumentStatus.READY.value)
            db.commit()
            logger.info(
                "DocumentParsingService — parsing succeeded for %s (%d chars extracted)",
                document_id,
                len(extracted_text),
            )
        except Exception as exc:
            db.rollback()
            logger.exception(
                "DocumentParsingService — parsing failed for %s: %s", document_id, exc
            )
            # Record failure in ParsedDocument
            try:
                create_parsed_document(
                    db,
                    document_id=document.id,
                    text_content="",
                    status=ParsedDocumentStatus.FAILED.value,
                )
                cls._set_document_status(db, document, DocumentStatus.FAILED.value)
                db.commit()
            except Exception:
                db.rollback()
                logger.exception(
                    "DocumentParsingService — failed to record failure state for %s",
                    document_id,
                )
            raise
