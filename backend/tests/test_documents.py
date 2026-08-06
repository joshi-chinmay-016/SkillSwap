"""
Day 66 Document Management — Comprehensive Test Suite.

Test coverage:
    - Model: constraints, enum values, relationships
    - Repository: create, rename, archive, retrieval, pagination, checksum lookup
    - Service: upload validation, duplicate detection, ownership, MIME validation
    - API: upload, download, rename, delete, list, pagination
    - Security: cross-user access (403), executable upload (415), path traversal rejection
    - Storage: provider save/read/stream/delete/exists, factory, health

Uses:
    - SQLite in-memory database (no PostgreSQL required)
    - Dependency override pattern (matches existing test suite)
    - MagicMock for storage provider isolation
"""
from __future__ import annotations

import io
import uuid
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
import tempfile
import os

import pytest
from fastapi import UploadFile
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.core.database import get_db
from app.dependencies.current_user import get_current_user
from app.models.base import Base
from app.models.user import User
from app.models.document import Document, DocumentStatus


# ──────────────────────────────────────────────────────────────────────────────
# Test Database Setup
# ──────────────────────────────────────────────────────────────────────────────

TEST_DB_URL = "sqlite:///:memory:"
# Use a single shared connection for the in-memory SQLite database.
# In-memory SQLite: each connection gets its own separate database.
# Sharing one connection ensures DDL (CREATE TABLE) is visible to DML (INSERT/SELECT).
from sqlalchemy import event
_test_engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})

@event.listens_for(_test_engine, "connect")
def connect(dbapi_connection, connection_record):
    connection_record.info["pid"] = os.getpid()

# Use StaticPool to keep a single connection across all sessions
from sqlalchemy.pool import StaticPool
_test_engine = create_engine(
    TEST_DB_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,  # ensures all sessions share the same connection
)
_TestSession = sessionmaker(autocommit=False, autoflush=False, bind=_test_engine)


def _create_test_tables():
    """Create only the tables needed for document tests.
    
    We cannot use Base.metadata.create_all() because other models in the project
    (market/trade models) use SQLAlchemy's UUID type which SQLite does not support.
    We create just User and Document tables directly.
    """
    from sqlalchemy import text
    with _test_engine.connect() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                email VARCHAR(255) NOT NULL UNIQUE,
                password_hash VARCHAR(255) NOT NULL,
                oauth_provider VARCHAR(50)
            )
        """))
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS documents (
                id VARCHAR(36) PRIMARY KEY,
                user_id INTEGER NOT NULL,
                original_filename VARCHAR(512) NOT NULL,
                stored_filename VARCHAR(255) NOT NULL,
                display_name VARCHAR(255) NOT NULL,
                file_extension VARCHAR(10) NOT NULL,
                mime_type VARCHAR(100) NOT NULL,
                file_size BIGINT NOT NULL,
                storage_path VARCHAR(1024) NOT NULL,
                checksum VARCHAR(64) NOT NULL,
                status VARCHAR(20) NOT NULL DEFAULT 'UPLOADED',
                uploaded_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                deleted_at DATETIME,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """))
        conn.commit()


def _drop_test_tables():
    """Drop the test tables."""
    from sqlalchemy import text
    with _test_engine.connect() as conn:
        conn.execute(text("DROP TABLE IF EXISTS documents"))
        conn.execute(text("DROP TABLE IF EXISTS users"))
        conn.commit()


def _get_test_db():
    db = _TestSession()
    try:
        yield db
    finally:
        db.close()


def _create_test_user(db, user_id: int = 1, email: str = "test@example.com") -> User:
    """Create and persist a minimal User for testing."""
    user = User(
        id=user_id,
        name="Test User",
        email=email,
        password_hash="hashed",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _create_test_document(db, user_id: int = 1, **overrides) -> Document:
    """Create and persist a minimal Document for testing."""
    doc_id = str(uuid.uuid4())
    doc = Document(
        id=doc_id,
        user_id=user_id,
        original_filename=overrides.get("original_filename", "test.pdf"),
        stored_filename=overrides.get("stored_filename", f"{doc_id}.pdf"),
        display_name=overrides.get("display_name", "test"),
        file_extension=overrides.get("file_extension", "pdf"),
        mime_type=overrides.get("mime_type", "application/pdf"),
        file_size=overrides.get("file_size", 1024),
        storage_path=overrides.get("storage_path", f"{user_id}/{doc_id}.pdf"),
        checksum=overrides.get("checksum", "abc123" + "0" * 58),
        status=overrides.get("status", DocumentStatus.UPLOADED.value),
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return doc


# ──────────────────────────────────────────────────────────────────────────────
# PART 1 — Model Tests
# ──────────────────────────────────────────────────────────────────────────────

class TestDocumentModel:
    """Verify model constraints, enum values, and defaults."""

    def setup_method(self):
        _create_test_tables()

    def teardown_method(self):
        _drop_test_tables()

    def test_document_status_enum_values(self):
        assert DocumentStatus.UPLOADED.value == "UPLOADED"
        assert DocumentStatus.PROCESSING.value == "PROCESSING"
        assert DocumentStatus.READY.value == "READY"
        assert DocumentStatus.FAILED.value == "FAILED"
        assert DocumentStatus.ARCHIVED.value == "ARCHIVED"

    def test_document_status_is_string_enum(self):
        """DocumentStatus should be usable as a string."""
        assert str(DocumentStatus.UPLOADED) == "DocumentStatus.UPLOADED"
        assert DocumentStatus.UPLOADED == "UPLOADED"

    def test_document_default_status(self):
        db = _TestSession()
        try:
            _create_test_user(db)
            doc = _create_test_document(db)
            assert doc.status == DocumentStatus.UPLOADED.value
        finally:
            db.close()

    def test_document_uuid_primary_key(self):
        db = _TestSession()
        try:
            _create_test_user(db)
            doc = _create_test_document(db)
            # UUID format: 8-4-4-4-12
            parts = doc.id.split("-")
            assert len(parts) == 5
        finally:
            db.close()

    def test_document_deleted_at_nullable(self):
        db = _TestSession()
        try:
            _create_test_user(db)
            doc = _create_test_document(db)
            assert doc.deleted_at is None
        finally:
            db.close()

    def test_document_repr(self):
        doc = Document(
            id="test-id",
            user_id=1,
            display_name="My Notes",
            status="UPLOADED",
        )
        assert "test-id" in repr(doc)
        assert "My Notes" in repr(doc)


# ──────────────────────────────────────────────────────────────────────────────
# PART 2 — Repository Tests
# ──────────────────────────────────────────────────────────────────────────────

class TestDocumentRepository:
    """Verify CRUD, pagination, checksum lookup."""

    def setup_method(self):
        _create_test_tables()
        self.db = _TestSession()
        _create_test_user(self.db, user_id=1)
        _create_test_user(self.db, user_id=2, email="user2@example.com")

    def teardown_method(self):
        self.db.close()
        _drop_test_tables()

    def test_create_document(self):
        from app.repositories.document_repository import create_document
        doc_id = str(uuid.uuid4())
        doc = create_document(
            self.db,
            id=doc_id,
            user_id=1,
            original_filename="notes.pdf",
            stored_filename=f"{doc_id}.pdf",
            display_name="notes",
            file_extension="pdf",
            mime_type="application/pdf",
            file_size=2048,
            storage_path=f"1/{doc_id}.pdf",
            checksum="a" * 64,
        )
        self.db.commit()
        assert doc.id == doc_id
        assert doc.user_id == 1
        assert doc.display_name == "notes"
        assert doc.status == DocumentStatus.UPLOADED.value

    def test_get_document(self):
        from app.repositories.document_repository import get_document
        doc = _create_test_document(self.db)
        found = get_document(self.db, doc.id)
        assert found is not None
        assert found.id == doc.id

    def test_get_document_missing_returns_none(self):
        from app.repositories.document_repository import get_document
        result = get_document(self.db, "nonexistent-id")
        assert result is None

    def test_get_user_document_ownership(self):
        from app.repositories.document_repository import get_user_document
        doc = _create_test_document(self.db, user_id=1)
        # Correct owner
        found = get_user_document(self.db, doc.id, user_id=1)
        assert found is not None
        # Wrong owner
        not_found = get_user_document(self.db, doc.id, user_id=2)
        assert not_found is None

    def test_update_document_display_name(self):
        from app.repositories.document_repository import update_document
        doc = _create_test_document(self.db)
        updated = update_document(self.db, doc, display_name="New Name")
        self.db.commit()
        assert updated.display_name == "New Name"

    def test_archive_document(self):
        from app.repositories.document_repository import archive_document
        doc = _create_test_document(self.db)
        archived = archive_document(self.db, doc)
        self.db.commit()
        assert archived.status == DocumentStatus.ARCHIVED.value
        assert archived.deleted_at is not None

    def test_find_by_checksum_same_user(self):
        from app.repositories.document_repository import find_by_checksum
        checksum = "b" * 64
        doc = _create_test_document(self.db, checksum=checksum, user_id=1)
        found = find_by_checksum(self.db, checksum=checksum, user_id=1)
        assert found is not None
        assert found.id == doc.id

    def test_find_by_checksum_different_user_returns_none(self):
        from app.repositories.document_repository import find_by_checksum
        checksum = "c" * 64
        _create_test_document(self.db, checksum=checksum, user_id=1)
        # Different user should not find the same checksum
        not_found = find_by_checksum(self.db, checksum=checksum, user_id=2)
        assert not_found is None

    def test_find_by_checksum_archived_excluded(self):
        from app.repositories.document_repository import archive_document, find_by_checksum
        checksum = "d" * 64
        doc = _create_test_document(self.db, checksum=checksum, user_id=1)
        archive_document(self.db, doc)
        self.db.commit()
        result = find_by_checksum(self.db, checksum=checksum, user_id=1)
        assert result is None

    def test_list_documents_pagination(self):
        from app.repositories.document_repository import list_documents
        for i in range(5):
            _create_test_document(
                self.db,
                user_id=1,
                checksum=("e" + str(i)) * 32,
                original_filename=f"file{i}.pdf",
                storage_path=f"1/file{i}.pdf",
            )
        docs, total = list_documents(self.db, user_id=1, page=1, page_size=3)
        assert total == 5
        assert len(docs) == 3

        docs_p2, _ = list_documents(self.db, user_id=1, page=2, page_size=3)
        assert len(docs_p2) == 2

    def test_list_documents_excludes_archived(self):
        from app.repositories.document_repository import list_documents, archive_document
        doc = _create_test_document(self.db, user_id=1)
        archive_document(self.db, doc)
        self.db.commit()
        docs, total = list_documents(self.db, user_id=1)
        assert total == 0

    def test_list_documents_sort_name(self):
        from app.repositories.document_repository import list_documents
        for name, ck in [("Zebra", "z" * 64), ("Apple", "a" * 64)]:
            _create_test_document(
                self.db, user_id=1, display_name=name,
                checksum=ck, original_filename=f"{name}.pdf",
                storage_path=f"1/{name}.pdf",
            )
        docs, _ = list_documents(self.db, user_id=1, sort="name")
        assert docs[0].display_name == "Apple"
        assert docs[1].display_name == "Zebra"

    def test_count_user_documents(self):
        from app.repositories.document_repository import count_user_documents
        _create_test_document(self.db, user_id=1, checksum="f" * 64)
        _create_test_document(self.db, user_id=1, checksum="g" * 64, original_filename="b.txt", storage_path="1/b.txt")
        count = count_user_documents(self.db, user_id=1)
        assert count == 2


# ──────────────────────────────────────────────────────────────────────────────
# PART 3 — Utility Tests
# ──────────────────────────────────────────────────────────────────────────────

class TestFileValidation:
    """Validate the file_validation utility functions."""

    def test_allowed_extensions(self):
        from app.utils.file_validation import validate_file_extension
        assert validate_file_extension("notes.pdf") == "pdf"
        assert validate_file_extension("readme.txt") == "txt"
        assert validate_file_extension("guide.md") == "md"
        assert validate_file_extension("NOTES.PDF") == "pdf"

    def test_rejected_extension_exe(self):
        from app.utils.file_validation import validate_file_extension
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc_info:
            validate_file_extension("malware.exe")
        assert exc_info.value.status_code == 415

    def test_rejected_extension_docx(self):
        from app.utils.file_validation import validate_file_extension
        from fastapi import HTTPException
        with pytest.raises(HTTPException):
            validate_file_extension("document.docx")

    def test_rejected_extension_zip(self):
        from app.utils.file_validation import validate_file_extension
        from fastapi import HTTPException
        with pytest.raises(HTTPException):
            validate_file_extension("archive.zip")

    def test_mime_pdf_valid(self):
        from app.utils.file_validation import validate_mime_type
        result = validate_mime_type("application/pdf", "pdf")
        assert result == "application/pdf"

    def test_mime_txt_valid(self):
        from app.utils.file_validation import validate_mime_type
        result = validate_mime_type("text/plain", "txt")
        assert result == "text/plain"

    def test_mime_md_valid_variants(self):
        from app.utils.file_validation import validate_mime_type
        # text/markdown
        assert validate_mime_type("text/markdown", "md") == "text/markdown"
        # text/plain with .md extension is also valid
        assert validate_mime_type("text/plain", "md") == "text/plain"

    def test_mime_spoofing_rejected(self):
        """A file with .pdf extension but octet-stream MIME should be rejected."""
        from app.utils.file_validation import validate_mime_type
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc_info:
            validate_mime_type("application/octet-stream", "pdf")
        assert exc_info.value.status_code == 415

    def test_exe_masquerading_as_pdf_rejected(self):
        """application/x-msdownload with .pdf extension — MIME mismatch."""
        from app.utils.file_validation import validate_mime_type
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc_info:
            validate_mime_type("application/x-msdownload", "pdf")
        assert exc_info.value.status_code == 415

    def test_file_size_within_limit(self):
        from app.utils.file_validation import validate_file_size
        # Should not raise
        validate_file_size(1024, max_bytes=26_214_400)

    def test_file_size_exceeds_limit(self):
        from app.utils.file_validation import validate_file_size
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc_info:
            validate_file_size(30_000_000, max_bytes=26_214_400)
        assert exc_info.value.status_code == 413

    def test_sanitize_filename_path_traversal(self):
        from app.utils.file_validation import sanitize_filename
        result = sanitize_filename("../../etc/passwd")
        assert ".." not in result
        assert result == "passwd"

    def test_sanitize_filename_null_bytes(self):
        from app.utils.file_validation import sanitize_filename
        result = sanitize_filename("file\x00name.pdf")
        assert "\x00" not in result

    def test_generate_stored_filename(self):
        from app.utils.file_validation import generate_stored_filename
        doc_id = "test-uuid-1234"
        result = generate_stored_filename(doc_id, "pdf")
        assert result == "test-uuid-1234.pdf"

    def test_build_display_name(self):
        from app.utils.file_validation import build_display_name
        assert build_display_name("Algorithms Notes.pdf") == "Algorithms Notes"
        assert build_display_name("readme.MD") == "readme"


class TestChecksum:
    """Verify checksum utility."""

    def test_calculate_sha256_deterministic(self):
        from app.utils.checksum import calculate_sha256
        data = b"hello world"
        h1 = calculate_sha256(data)
        h2 = calculate_sha256(data)
        assert h1 == h2
        assert len(h1) == 64  # SHA-256 → 64 hex chars

    def test_calculate_sha256_different_inputs(self):
        from app.utils.checksum import calculate_sha256
        assert calculate_sha256(b"aaa") != calculate_sha256(b"bbb")

    def test_calculate_sha256_known_value(self):
        from app.utils.checksum import calculate_sha256
        import hashlib
        data = b"test content"
        expected = hashlib.sha256(data).hexdigest()
        assert calculate_sha256(data) == expected


# ──────────────────────────────────────────────────────────────────────────────
# PART 4 — Storage Provider Tests
# ──────────────────────────────────────────────────────────────────────────────

class TestLocalStorageProvider:
    """Verify LocalStorageProvider file IO operations."""

    def setup_method(self):
        self.tmp_dir = tempfile.mkdtemp()
        from app.storage.local_storage_provider import LocalStorageProvider
        self.provider = LocalStorageProvider(self.tmp_dir)

    def teardown_method(self):
        import shutil
        shutil.rmtree(self.tmp_dir, ignore_errors=True)

    def test_save_and_exists(self):
        file_data = b"Hello PDF"
        doc_id = str(uuid.uuid4())
        meta = self.provider.save_file(file_data, user_id=1, document_id=doc_id, extension="pdf")
        assert meta.exists is True
        assert meta.size == len(file_data)
        assert self.provider.exists(meta.storage_path) is True

    def test_save_creates_user_directory(self):
        doc_id = str(uuid.uuid4())
        self.provider.save_file(b"data", user_id=99, document_id=doc_id, extension="txt")
        user_dir = Path(self.tmp_dir) / "99"
        assert user_dir.exists()

    def test_get_file_returns_bytes(self):
        data = b"file content"
        doc_id = str(uuid.uuid4())
        meta = self.provider.save_file(data, user_id=1, document_id=doc_id, extension="txt")
        retrieved = self.provider.get_file(meta.storage_path)
        assert retrieved == data

    def test_delete_file(self):
        doc_id = str(uuid.uuid4())
        meta = self.provider.save_file(b"del me", user_id=1, document_id=doc_id, extension="md")
        assert self.provider.exists(meta.storage_path)
        deleted = self.provider.delete_file(meta.storage_path)
        assert deleted is True
        assert not self.provider.exists(meta.storage_path)

    def test_delete_nonexistent_returns_false(self):
        result = self.provider.delete_file("1/nonexistent.pdf")
        assert result is False

    def test_path_traversal_rejected(self):
        from app.exceptions.storage_exceptions import StorageValidationError
        with pytest.raises(StorageValidationError):
            self.provider.get_file("../../etc/passwd")

    def test_generate_storage_path(self):
        path = self.provider.generate_storage_path(42, "uuid-123", "pdf")
        assert path == "42/uuid-123.pdf"

    def test_get_file_metadata(self):
        data = b"metadata test"
        doc_id = str(uuid.uuid4())
        meta = self.provider.save_file(data, user_id=1, document_id=doc_id, extension="pdf")
        stat = self.provider.get_file_metadata(meta.storage_path)
        assert stat.size == len(data)
        assert stat.exists is True

    def test_checksum_in_metadata(self):
        from app.utils.checksum import calculate_sha256
        data = b"checksum data"
        doc_id = str(uuid.uuid4())
        meta = self.provider.save_file(data, user_id=1, document_id=doc_id, extension="txt")
        assert meta.checksum == calculate_sha256(data)

    def test_list_all_files(self):
        doc_id1 = str(uuid.uuid4())
        doc_id2 = str(uuid.uuid4())
        self.provider.save_file(b"a", user_id=1, document_id=doc_id1, extension="pdf")
        self.provider.save_file(b"b", user_id=2, document_id=doc_id2, extension="txt")
        all_files = self.provider.list_all_files()
        assert len(all_files) == 2


class TestStorageFactory:
    """Verify factory returns correct providers."""

    def test_local_provider_returned(self):
        from app.storage.storage_factory import StorageProviderFactory
        from app.storage.local_storage_provider import LocalStorageProvider
        provider = StorageProviderFactory.get_provider("LOCAL")
        assert isinstance(provider, LocalStorageProvider)

    def test_unknown_provider_raises(self):
        from app.storage.storage_factory import StorageProviderFactory
        from app.exceptions.storage_exceptions import StorageValidationError
        with pytest.raises(StorageValidationError):
            StorageProviderFactory.get_provider("S3")


class TestStorageHealthService:
    """Verify health checks work for local provider."""

    def setup_method(self):
        self.tmp_dir = tempfile.mkdtemp()
        from app.storage.local_storage_provider import LocalStorageProvider
        from app.storage.storage_health_service import StorageHealthService
        self.provider = LocalStorageProvider(self.tmp_dir)
        self.health = StorageHealthService(self.provider)

    def teardown_method(self):
        import shutil
        shutil.rmtree(self.tmp_dir, ignore_errors=True)

    def test_healthy_directory(self):
        report = self.health.check()
        assert report.healthy is True
        assert report.directory_exists is True
        assert report.directory_readable is True
        assert report.directory_writable is True

    def test_health_report_has_disk_info(self):
        report = self.health.check()
        assert report.disk_total_bytes is not None
        assert report.disk_free_bytes is not None


# ──────────────────────────────────────────────────────────────────────────────
# PART 5 — API Tests
# ──────────────────────────────────────────────────────────────────────────────

class TestDocumentAPI:
    """
    End-to-end API tests using FastAPI TestClient.

    Pattern matches existing test_mentor_memory_api.py:
        - dependency_overrides for auth + DB
        - MagicMock for DB where full persistence is not needed
        - Real DB for upload/download flow tests
    """

    def setup_method(self):
        _create_test_tables()
        self.client = TestClient(app)
        self.mock_user = MagicMock()
        self.mock_user.id = 1

    def teardown_method(self):
        app.dependency_overrides.clear()
        _drop_test_tables()

    # ── Authentication guard ──────────────────────────────────────────────────

    def test_upload_unauthenticated(self):
        res = self.client.post("/documents/upload")
        assert res.status_code == 401

    def test_list_unauthenticated(self):
        res = self.client.get("/documents")
        assert res.status_code == 401

    def test_get_unauthenticated(self):
        res = self.client.get("/documents/some-id")
        assert res.status_code == 401

    # ── Upload ────────────────────────────────────────────────────────────────

    def test_upload_pdf_success(self):
        """Full upload flow with real in-memory DB and temp storage."""
        from app.storage.local_storage_provider import LocalStorageProvider
        from app.storage.storage_service import StorageService

        with tempfile.TemporaryDirectory() as tmp_dir:
            real_storage = StorageService(LocalStorageProvider(tmp_dir))

            # Set up real DB
            db = _TestSession()
            _create_test_user(db, user_id=1)

            def override_db():
                yield db

            def override_user():
                return db.query(User).filter_by(id=1).first()

            # Patch storage_service inside document_service
            with patch("app.services.document_service._default_storage", real_storage):
                app.dependency_overrides[get_db] = override_db
                app.dependency_overrides[get_current_user] = override_user

                try:
                    pdf_bytes = b"%PDF-1.4 test content"
                    res = self.client.post(
                        "/documents/upload",
                        files={"file": ("notes.pdf", pdf_bytes, "application/pdf")},
                    )
                    assert res.status_code == 201
                    data = res.json()
                    assert data["display_name"] == "notes"
                    assert data["status"] == "UPLOADED"
                    assert data["mime_type"] == "application/pdf"
                    assert "id" in data
                    assert "checksum" not in data
                    assert "storage_path" not in data
                finally:
                    db.close()

    def test_upload_unsupported_extension(self):
        app.dependency_overrides[get_current_user] = lambda: self.mock_user
        app.dependency_overrides[get_db] = lambda: MagicMock()

        try:
            res = self.client.post(
                "/documents/upload",
                files={"file": ("malware.exe", b"MZ...", "application/x-msdownload")},
            )
            assert res.status_code == 415
        finally:
            app.dependency_overrides.clear()

    def test_upload_docx_rejected(self):
        app.dependency_overrides[get_current_user] = lambda: self.mock_user
        app.dependency_overrides[get_db] = lambda: MagicMock()

        try:
            res = self.client.post(
                "/documents/upload",
                files={"file": ("essay.docx", b"PK\x03\x04...", "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
            )
            assert res.status_code == 415
        finally:
            app.dependency_overrides.clear()

    def test_upload_zip_rejected(self):
        app.dependency_overrides[get_current_user] = lambda: self.mock_user
        app.dependency_overrides[get_db] = lambda: MagicMock()

        try:
            res = self.client.post(
                "/documents/upload",
                files={"file": ("archive.zip", b"PK\x03\x04", "application/zip")},
            )
            assert res.status_code == 415
        finally:
            app.dependency_overrides.clear()

    def test_upload_path_traversal_filename(self):
        """A path traversal filename should be sanitized — not crash or store dangerously."""
        from app.storage.local_storage_provider import LocalStorageProvider
        from app.storage.storage_service import StorageService

        with tempfile.TemporaryDirectory() as tmp_dir:
            real_storage = StorageService(LocalStorageProvider(tmp_dir))

            db = _TestSession()
            _create_test_user(db, user_id=1)

            def override_db():
                yield db

            def override_user():
                return db.query(User).filter_by(id=1).first()

            with patch("app.services.document_service._default_storage", real_storage):
                app.dependency_overrides[get_db] = override_db
                app.dependency_overrides[get_current_user] = override_user

                try:
                    res = self.client.post(
                        "/documents/upload",
                        # Path traversal in filename — should be sanitized to "passwd.pdf"
                        files={"file": ("../../etc/passwd.pdf", b"%PDF-1.4 x", "application/pdf")},
                    )
                    # Either it succeeds with sanitized name or 415 — NOT a server error
                    assert res.status_code in (201, 415)
                    if res.status_code == 201:
                        data = res.json()
                        # Must never have ".." in the stored filename
                        assert ".." not in data.get("original_filename", "")
                finally:
                    db.close()

    # ── List ──────────────────────────────────────────────────────────────────

    def test_list_documents_authenticated(self):
        mock_db = MagicMock()

        # Set up mock service response
        from app.schemas.document import DocumentListResponse
        with patch("app.api.document_router.service.list_documents") as mock_list:
            mock_list.return_value = DocumentListResponse(
                documents=[],
                total=0,
                page=1,
                page_size=20,
                has_next=False,
                has_previous=False,
            )
            app.dependency_overrides[get_current_user] = lambda: self.mock_user
            app.dependency_overrides[get_db] = lambda: mock_db

            try:
                res = self.client.get("/documents")
                assert res.status_code == 200
                data = res.json()
                assert "documents" in data
                assert "total" in data
                assert "page" in data
            finally:
                app.dependency_overrides.clear()

    def test_list_documents_pagination_params(self):
        mock_db = MagicMock()
        from app.schemas.document import DocumentListResponse
        with patch("app.api.document_router.service.list_documents") as mock_list:
            mock_list.return_value = DocumentListResponse(
                documents=[],
                total=0,
                page=2,
                page_size=5,
                has_next=False,
                has_previous=True,
            )
            app.dependency_overrides[get_current_user] = lambda: self.mock_user
            app.dependency_overrides[get_db] = lambda: mock_db

            try:
                res = self.client.get("/documents?page=2&page_size=5")
                assert res.status_code == 200
                data = res.json()
                assert data["page"] == 2
                assert data["page_size"] == 5
                assert data["has_previous"] is True
            finally:
                app.dependency_overrides.clear()

    # ── Get document ──────────────────────────────────────────────────────────

    def test_get_document_not_found(self):
        db = _TestSession()
        _create_test_user(db, user_id=1)

        def override_db():
            yield db

        def override_user():
            return db.query(User).filter_by(id=1).first()

        app.dependency_overrides[get_db] = override_db
        app.dependency_overrides[get_current_user] = override_user

        try:
            res = self.client.get("/documents/nonexistent-uuid")
            assert res.status_code == 404
        finally:
            db.close()

    def test_get_document_success(self):
        db = _TestSession()
        _create_test_user(db, user_id=1)
        doc = _create_test_document(db, user_id=1)

        def override_db():
            yield db

        def override_user():
            return db.query(User).filter_by(id=1).first()

        app.dependency_overrides[get_db] = override_db
        app.dependency_overrides[get_current_user] = override_user

        try:
            res = self.client.get(f"/documents/{doc.id}")
            assert res.status_code == 200
            data = res.json()
            assert data["id"] == doc.id
            assert "checksum" not in data
            assert "storage_path" not in data
        finally:
            db.close()

    # ── Rename ────────────────────────────────────────────────────────────────

    def test_rename_document(self):
        db = _TestSession()
        _create_test_user(db, user_id=1)
        doc = _create_test_document(db, user_id=1)

        def override_db():
            yield db

        def override_user():
            return db.query(User).filter_by(id=1).first()

        app.dependency_overrides[get_db] = override_db
        app.dependency_overrides[get_current_user] = override_user

        try:
            res = self.client.patch(
                f"/documents/{doc.id}",
                json={"display_name": "Renamed Notes"},
            )
            assert res.status_code == 200
            data = res.json()
            assert data["display_name"] == "Renamed Notes"
        finally:
            db.close()

    def test_rename_validates_empty_name(self):
        db = _TestSession()
        _create_test_user(db, user_id=1)
        doc = _create_test_document(db, user_id=1)

        def override_db():
            yield db

        def override_user():
            return db.query(User).filter_by(id=1).first()

        app.dependency_overrides[get_db] = override_db
        app.dependency_overrides[get_current_user] = override_user

        try:
            res = self.client.patch(
                f"/documents/{doc.id}",
                json={"display_name": ""},
            )
            assert res.status_code == 422  # Validation error
        finally:
            db.close()

    # ── Delete ────────────────────────────────────────────────────────────────

    def test_delete_document_soft(self):
        db = _TestSession()
        _create_test_user(db, user_id=1)
        doc = _create_test_document(db, user_id=1)

        def override_db():
            yield db

        def override_user():
            return db.query(User).filter_by(id=1).first()

        app.dependency_overrides[get_db] = override_db
        app.dependency_overrides[get_current_user] = override_user

        try:
            res = self.client.delete(f"/documents/{doc.id}")
            assert res.status_code == 200
            data = res.json()
            assert data["status"] == "ARCHIVED"
            assert data["id"] == doc.id

            # Verify document is now archived in DB
            from sqlalchemy.orm import Session
            refreshed = db.query(Document).filter_by(id=doc.id).first()
            assert refreshed.status == DocumentStatus.ARCHIVED.value
            assert refreshed.deleted_at is not None
        finally:
            db.close()

    # ── Health & Metrics ─────────────────────────────────────────────────────

    def test_storage_health_endpoint(self):
        app.dependency_overrides[get_current_user] = lambda: self.mock_user

        try:
            res = self.client.get("/documents/health")
            assert res.status_code == 200
            data = res.json()
            assert "healthy" in data
            assert "provider" in data
            assert "directory_exists" in data
        finally:
            app.dependency_overrides.clear()

    def test_metrics_endpoint(self):
        app.dependency_overrides[get_current_user] = lambda: self.mock_user

        try:
            res = self.client.get("/documents/metrics")
            assert res.status_code == 200
            data = res.json()
            assert "uploads_total" in data
            assert "uploads_failed" in data
            assert "downloads_total" in data
        finally:
            app.dependency_overrides.clear()


# ──────────────────────────────────────────────────────────────────────────────
# PART 6 — Security Tests
# ──────────────────────────────────────────────────────────────────────────────

class TestDocumentSecurity:
    """
    Critical security tests.

    These must ALL pass without exception:
        1. User A cannot access User B's document.
        2. Executable uploads must be rejected.
        3. Path traversal filenames must be sanitised or rejected.
    """

    def setup_method(self):
        _create_test_tables()
        self.client = TestClient(app)
        self.db = _TestSession()
        _create_test_user(self.db, user_id=1, email="user1@example.com")
        _create_test_user(self.db, user_id=2, email="user2@example.com")

    def teardown_method(self):
        app.dependency_overrides.clear()
        self.db.close()
        _drop_test_tables()

    def test_user_a_cannot_get_user_b_document(self):
        """User A (id=2) attempts to GET User B's (id=1) document → 403."""
        user_b_doc = _create_test_document(self.db, user_id=1)
        user_a = self.db.query(User).filter_by(id=2).first()

        def override_db():
            yield self.db

        def override_user_a():
            return user_a

        app.dependency_overrides[get_db] = override_db
        app.dependency_overrides[get_current_user] = override_user_a

        res = self.client.get(f"/documents/{user_b_doc.id}")
        assert res.status_code == 403, (
            f"SECURITY VIOLATION: User A accessed User B's document! Status: {res.status_code}"
        )

    def test_user_a_cannot_rename_user_b_document(self):
        """User A (id=2) attempts to PATCH User B's (id=1) document → 403."""
        user_b_doc = _create_test_document(self.db, user_id=1)
        user_a = self.db.query(User).filter_by(id=2).first()

        def override_db():
            yield self.db

        def override_user_a():
            return user_a

        app.dependency_overrides[get_db] = override_db
        app.dependency_overrides[get_current_user] = override_user_a

        res = self.client.patch(
            f"/documents/{user_b_doc.id}",
            json={"display_name": "Stolen"},
        )
        assert res.status_code == 403, (
            f"SECURITY VIOLATION: User A renamed User B's document! Status: {res.status_code}"
        )

    def test_user_a_cannot_delete_user_b_document(self):
        """User A (id=2) attempts to DELETE User B's (id=1) document → 403."""
        user_b_doc = _create_test_document(self.db, user_id=1)
        user_a = self.db.query(User).filter_by(id=2).first()

        def override_db():
            yield self.db

        def override_user_a():
            return user_a

        app.dependency_overrides[get_db] = override_db
        app.dependency_overrides[get_current_user] = override_user_a

        res = self.client.delete(f"/documents/{user_b_doc.id}")
        assert res.status_code == 403, (
            f"SECURITY VIOLATION: User A deleted User B's document! Status: {res.status_code}"
        )

    def test_upload_executable_rejected(self):
        """Uploading an .exe file must always return 415."""
        user = self.db.query(User).filter_by(id=1).first()

        def override_db():
            yield self.db

        def override_user():
            return user

        app.dependency_overrides[get_db] = override_db
        app.dependency_overrides[get_current_user] = override_user

        res = self.client.post(
            "/documents/upload",
            files={"file": ("virus.exe", b"MZ\x90\x00", "application/x-msdownload")},
        )
        assert res.status_code == 415, (
            f"SECURITY VIOLATION: Executable was accepted! Status: {res.status_code}"
        )

    def test_upload_script_rejected(self):
        """Uploading a .sh shell script must be rejected."""
        user = self.db.query(User).filter_by(id=1).first()

        def override_db():
            yield self.db

        def override_user():
            return user

        app.dependency_overrides[get_db] = override_db
        app.dependency_overrides[get_current_user] = override_user

        res = self.client.post(
            "/documents/upload",
            files={"file": ("hack.sh", b"#!/bin/bash\nrm -rf /", "text/x-sh")},
        )
        assert res.status_code == 415

    def test_upload_duplicate_rejected(self):
        """Same user uploading the same file twice → 409."""
        from app.storage.local_storage_provider import LocalStorageProvider
        from app.storage.storage_service import StorageService

        with tempfile.TemporaryDirectory() as tmp_dir:
            real_storage = StorageService(LocalStorageProvider(tmp_dir))
            user = self.db.query(User).filter_by(id=1).first()

            def override_db():
                yield self.db

            def override_user():
                return user

            with patch("app.services.document_service._default_storage", real_storage):
                app.dependency_overrides[get_db] = override_db
                app.dependency_overrides[get_current_user] = override_user

                pdf_bytes = b"%PDF-1.4 identical content for duplicate test"

                res1 = self.client.post(
                    "/documents/upload",
                    files={"file": ("notes.pdf", pdf_bytes, "application/pdf")},
                )
                assert res1.status_code == 201

                res2 = self.client.post(
                    "/documents/upload",
                    files={"file": ("notes.pdf", pdf_bytes, "application/pdf")},
                )
                assert res2.status_code == 409, (
                    f"Duplicate upload was accepted! Status: {res2.status_code}"
                )
