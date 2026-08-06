"""
Document — SQLAlchemy model for learner-uploaded documents (Day 66 Part A1).

Relationships:
    User  1 ──── * Document

Every document belongs to exactly one authenticated user.
Ownership is enforced at the service layer on every operation.

Status lifecycle:
    UPLOADED → PROCESSING → READY → FAILED
    Any status → ARCHIVED  (soft delete)

Future:
    Day 67: status transitions UPLOADED → PROCESSING → READY / FAILED
            as the parser produces extracted text.
    Day 68-70: embedding pipeline consumes READY documents via storage_path.
    Day 66 Part A2: storage_path is resolved through StorageService —
                    never accessed directly from this model.
"""
from __future__ import annotations

import enum
import uuid
from datetime import datetime
from typing import Optional

import sqlalchemy as sa
from sqlalchemy import (
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
    BigInteger,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


# ── Enums ─────────────────────────────────────────────────────────────────────

class DocumentStatus(str, enum.Enum):
    """
    Lifecycle status of a document.

    UPLOADED    — file received and stored; no processing yet.
    PROCESSING  — parser is extracting text (Day 67+).
    READY       — fully processed; available for RAG retrieval (Day 70+).
    FAILED      — processing failed; may be retried.
    ARCHIVED    — soft-deleted; hidden from user listings.
    """

    UPLOADED = "UPLOADED"
    PROCESSING = "PROCESSING"
    READY = "READY"
    FAILED = "FAILED"
    ARCHIVED = "ARCHIVED"


# ── Model ─────────────────────────────────────────────────────────────────────

class Document(Base):
    """
    One uploaded document belonging to exactly one User.

    Storage layout (managed by StorageService / LocalStorageProvider):
        uploads/{user_id}/{id}.{file_extension}

    Security notes:
        - ``stored_filename`` is always a UUID — never the original name.
        - ``storage_path`` is a provider-relative path; the physical
          location is never exposed to the API layer.
        - ``checksum`` is stored for duplicate detection and integrity
          validation but is NOT returned in API responses.
    """

    __tablename__ = "documents"

    # ── Identity ──────────────────────────────────────────────────────────────

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        comment="UUID v4 — matches the stored filename stem.",
    )

    # ── Ownership ─────────────────────────────────────────────────────────────

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Owner user ID — documents are invisible to other users.",
    )

    # ── Filenames ─────────────────────────────────────────────────────────────

    original_filename: Mapped[str] = mapped_column(
        String(512),
        nullable=False,
        comment="Raw filename as provided by the user (e.g. 'Algorithms Notes.pdf').",
    )

    stored_filename: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="UUID-based filename used on disk (e.g. 'uuid.pdf').",
    )

    display_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Human-readable name shown in the UI (stem of original_filename, renameable).",
    )

    # ── Type information ──────────────────────────────────────────────────────

    file_extension: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        comment="Lowercase extension without dot (e.g. 'pdf', 'txt', 'md').",
    )

    mime_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="Validated MIME type (e.g. 'application/pdf').",
    )

    # ── Size & storage ────────────────────────────────────────────────────────

    file_size: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        comment="File size in bytes.",
    )

    storage_path: Mapped[str] = mapped_column(
        String(1024),
        nullable=False,
        comment="Provider-relative path (e.g. '42/uuid.pdf'). Resolved by StorageService.",
    )

    # ── Integrity ─────────────────────────────────────────────────────────────

    checksum: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        index=True,
        comment="SHA-256 hex digest. Used for duplicate detection. NOT exposed in API.",
    )

    # ── Status ────────────────────────────────────────────────────────────────

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=DocumentStatus.UPLOADED.value,
        comment="Document lifecycle status.",
    )

    # ── Timestamps ────────────────────────────────────────────────────────────

    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=sa.func.now(),
        nullable=False,
        comment="When the file was first received.",
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=sa.func.now(),
        onupdate=sa.func.now(),
        nullable=False,
        comment="Last metadata update (rename, status change, etc.).",
    )

    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
        comment="Soft-delete timestamp. NULL = active. Set on ARCHIVE.",
    )

    # ── Relationships ─────────────────────────────────────────────────────────

    user = relationship(
        "User",
        back_populates="documents",
    )

    # Relationship to the parsed document (one-to-one)
    parsed_document = relationship(
        "ParsedDocument",
        uselist=False,
        back_populates="document",
    )

    # ── Indexes ───────────────────────────────────────────────────────────────

    __table_args__ = (
        Index("idx_document_user_id", "user_id"),
        Index("idx_document_status", "status"),
        Index("idx_document_checksum", "checksum"),
        Index("idx_document_user_status", "user_id", "status"),
        Index("idx_document_user_uploaded_at", "user_id", "uploaded_at"),
        # Composite unique: same checksum per user → duplicate rejection
        Index(
            "idx_document_user_checksum",
            "user_id",
            "checksum",
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<Document id={self.id!r} user_id={self.user_id} "
            f"display_name={self.display_name!r} status={self.status!r}>"
        )
