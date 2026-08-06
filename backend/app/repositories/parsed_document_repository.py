from __future__ import annotations

from typing import Optional

from sqlalchemy.orm import Session

from app.models.parsed_document import ParsedDocument, ParsedDocumentStatus


def create_parsed_document(
    db: Session,
    *,
    document_id: str,
    text_content: str,
    status: str = ParsedDocumentStatus.PENDING.value,
) -> ParsedDocument:
    parsed = ParsedDocument(
        document_id=document_id,
        text_content=text_content,
        status=status,
    )
    db.add(parsed)
    db.flush()
    return parsed


def get_parsed_document(db: Session, document_id: str) -> Optional[ParsedDocument]:
    return (
        db.query(ParsedDocument)
        .filter(ParsedDocument.document_id == document_id)
        .first()
    )


def update_parsed_document_status(
    db: Session, parsed: ParsedDocument, status: str
) -> ParsedDocument:
    parsed.status = status
    db.flush()
    return parsed
