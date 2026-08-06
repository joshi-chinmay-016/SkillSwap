"""
ParsedDocument — stores the raw text extracted by the parsing engine (Day 67).

Relationships:
    Document 1 ──── 1 ParsedDocument

Status lifecycle:
    PENDING  → READY   (text extraction succeeded)
    PENDING  → FAILED  (text extraction failed)
"""
from __future__ import annotations

import enum
import uuid
from datetime import datetime

import sqlalchemy as sa
from sqlalchemy import Column, DateTime, ForeignKey, String, Text, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class ParsedDocumentStatus(str, enum.Enum):
    PENDING = "PENDING"
    READY = "READY"
    FAILED = "FAILED"


class ParsedDocument(Base):
    __tablename__ = "parsed_documents"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    document_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    text_content: Mapped[str] = mapped_column(Text, nullable=False, default="")
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=ParsedDocumentStatus.PENDING.value,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=sa.func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()
    )

    document = relationship("Document", back_populates="parsed_document")

    def __repr__(self) -> str:
        return (
            f"<ParsedDocument id={self.id!r} document_id={self.document_id!r} "
            f"status={self.status!r} chars={len(self.text_content or '')}>"
        )
