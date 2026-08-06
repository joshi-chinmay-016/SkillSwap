"""
Day 67 Document Parsing Engine — Comprehensive Test Suite.

Test coverage:
    - Parsers: TxtParser, MarkdownParser, PDFParser
    - ParserFactory & ParserManager: format mapping, fallback, error handling
    - Repository: ParsedDocument CRUD
    - Service: DocumentParsingService status transitions & persistence
    - API: GET /documents/{id}/parsed endpoint (auth, ownership, status, 404)
"""
from __future__ import annotations

import io
import os
import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool


from app.main import app
from app.core.database import get_db
from app.dependencies.current_user import get_current_user
from app.models.base import Base
from app.models.user import User
from app.models.document import Document, DocumentStatus
from app.models.parsed_document import ParsedDocument, ParsedDocumentStatus
from app.repositories import parsed_document_repository as parsed_repo
from app.repositories import document_repository as doc_repo
from app.services.document_parsing_service import DocumentParsingService
from parsers.document_parser import DocumentParser
from parsers.txt_parser import TxtParser
from parsers.markdown_parser import MarkdownParser
from parsers.pdf_parser import PDFParser
from parsers.parser_factory import ParserFactory, UnsupportedFileTypeError
from parsers.parser_manager import ParserManager


# ──────────────────────────────────────────────────────────────────────────────
# Test Database Setup
# ──────────────────────────────────────────────────────────────────────────────

TEST_DB_URL = "sqlite:///:memory:"
_test_engine = create_engine(
    TEST_DB_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=_test_engine
)


def _create_test_tables():
    from sqlalchemy import text
    with _test_engine.connect() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                name VARCHAR(100),
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
                deleted_at DATETIME
            )
        """))
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS parsed_documents (
                id VARCHAR(36) PRIMARY KEY,
                document_id VARCHAR(36) NOT NULL UNIQUE,
                text_content TEXT NOT NULL,
                status VARCHAR(20) NOT NULL DEFAULT 'PENDING',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE
            )
        """))
        conn.commit()


@pytest.fixture(autouse=True)
def setup_db():
    """Create test tables before each test and drop them after."""
    _create_test_tables()

    def _override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = _override_get_db
    yield
    from sqlalchemy import text
    with _test_engine.connect() as conn:
        conn.execute(text("DROP TABLE IF EXISTS parsed_documents"))
        conn.execute(text("DROP TABLE IF EXISTS documents"))
        conn.execute(text("DROP TABLE IF EXISTS users"))
        conn.commit()
    app.dependency_overrides.pop(get_db, None)



@pytest.fixture
def db():
    """Provide a database session for tests."""
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def mock_user(db):
    """Create and return a dummy user."""
    user = User(
        id=101,
        email="learner@example.com",
        name="Learner Jane",
        password_hash="hashed_secret",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def mock_other_user(db):
    """Create and return a second user for cross-access checks."""
    user = User(
        id=102,
        email="other@example.com",
        name="Learner Bob",
        password_hash="hashed_secret",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user



@pytest.fixture
def client(mock_user):
    """TestClient authenticated as mock_user."""

    def _override_get_current_user():
        return mock_user

    app.dependency_overrides[get_current_user] = _override_get_current_user
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.pop(get_current_user, None)


# ──────────────────────────────────────────────────────────────────────────────
# 1. Unit Tests — Concrete Parsers
# ──────────────────────────────────────────────────────────────────────────────

def test_txt_parser_utf8():
    parser = TxtParser()
    content = "Hello, SkillSwap Arena!\nThis is plain text."
    result = parser.parse(content.encode("utf-8"))
    assert result == content


def test_txt_parser_latin1():
    parser = TxtParser()
    content = "Café & Résumé text."
    result = parser.parse(content.encode("latin-1"))
    assert "Caf" in result


def test_markdown_parser():
    parser = MarkdownParser()
    md_content = "# Header\n\nThis is **bold** text with a [link](http://example.com)."
    result = parser.parse(md_content.encode("utf-8"))
    assert "Header" in result
    assert "bold text" in result or "bold" in result
    assert "http://example.com" not in result  # Link target stripped in HTML tag conversion


def test_pdf_parser_valid():
    parser = PDFParser()
    try:
        import fitz
    except ImportError:
        pytest.skip("PyMuPDF (fitz) not installed")

    # Create an in-memory PDF using PyMuPDF
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 50), "Python RAG Architecture Notes")
    pdf_bytes = doc.tobytes()
    doc.close()

    result = parser.parse(pdf_bytes)
    assert "Python RAG Architecture Notes" in result



def test_pdf_parser_corrupt():
    parser = PDFParser()
    corrupt_bytes = b"Not a valid PDF header"
    with pytest.raises(ValueError, match="Unable to open PDF"):
        parser.parse(corrupt_bytes)


# ──────────────────────────────────────────────────────────────────────────────
# 2. Unit Tests — Factory & Manager
# ──────────────────────────────────────────────────────────────────────────────

def test_parser_factory_selection():
    assert isinstance(ParserFactory.get_parser("pdf"), PDFParser)
    assert isinstance(ParserFactory.get_parser(".TXT"), TxtParser)
    assert isinstance(ParserFactory.get_parser("md"), MarkdownParser)
    assert isinstance(ParserFactory.get_parser("markdown"), MarkdownParser)

    with pytest.raises(UnsupportedFileTypeError):
        ParserFactory.get_parser("exe")


def test_parser_manager():
    text = ParserManager.parse_document(b"Hello Manager", "txt")
    assert text == "Hello Manager"

    with pytest.raises(ValueError, match="No parser for extension"):
        ParserManager.parse_document(b"data", "invalid_ext")


# ──────────────────────────────────────────────────────────────────────────────
# 3. Repository Tests — ParsedDocument
# ──────────────────────────────────────────────────────────────────────────────

def test_parsed_document_repository(db, mock_user):
    # Create a document
    doc = doc_repo.create_document(
        db,
        id=str(uuid.uuid4()),
        user_id=mock_user.id,
        original_filename="notes.txt",
        stored_filename="notes.txt",
        display_name="notes",
        file_extension="txt",
        mime_type="text/plain",
        file_size=12,
        storage_path=f"{mock_user.id}/notes.txt",
        checksum="1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef",
    )
    db.commit()

    # Create parsed document
    parsed = parsed_repo.create_parsed_document(
        db,
        document_id=doc.id,
        text_content="Hello World",
        status=ParsedDocumentStatus.READY.value,
    )
    db.commit()

    # Fetch parsed document
    fetched = parsed_repo.get_parsed_document(db, doc.id)
    assert fetched is not None
    assert fetched.document_id == doc.id
    assert fetched.text_content == "Hello World"
    assert fetched.status == ParsedDocumentStatus.READY.value

    # Update status
    updated = parsed_repo.update_parsed_document_status(
        db, fetched, ParsedDocumentStatus.FAILED.value
    )
    db.commit()
    assert updated.status == ParsedDocumentStatus.FAILED.value


# ──────────────────────────────────────────────────────────────────────────────
# 4. Service Tests — DocumentParsingService
# ──────────────────────────────────────────────────────────────────────────────

def test_document_parsing_service_success(db, mock_user, monkeypatch):
    doc_id = str(uuid.uuid4())
    storage_path = f"{mock_user.id}/{doc_id}.txt"
    doc = doc_repo.create_document(
        db,
        id=doc_id,
        user_id=mock_user.id,
        original_filename="sample.txt",
        stored_filename=f"{doc_id}.txt",
        display_name="sample",
        file_extension="txt",
        mime_type="text/plain",
        file_size=18,
        storage_path=storage_path,
        checksum="abcdefabcdefabcdefabcdefabcdefabcdefabcdefabcdefabcdefabcdefabcd",
    )
    db.commit()

    # Mock storage service get_file
    from app.storage.storage_service import storage_service

    monkeypatch.setattr(
        storage_service, "get_file", lambda path: b"Sample text content"
    )

    # Process document
    DocumentParsingService.process_document(db, doc_id)

    # Verify Document status updated to READY
    db.refresh(doc)
    assert doc.status == DocumentStatus.READY.value

    # Verify ParsedDocument record
    parsed = parsed_repo.get_parsed_document(db, doc_id)
    assert parsed is not None
    assert parsed.text_content == "Sample text content"
    assert parsed.status == ParsedDocumentStatus.READY.value


def test_document_parsing_service_failure(db, mock_user, monkeypatch):
    doc_id = str(uuid.uuid4())
    storage_path = f"{mock_user.id}/{doc_id}.pdf"
    doc = doc_repo.create_document(
        db,
        id=doc_id,
        user_id=mock_user.id,
        original_filename="bad.pdf",
        stored_filename=f"{doc_id}.pdf",
        display_name="bad",
        file_extension="pdf",
        mime_type="application/pdf",
        file_size=20,
        storage_path=storage_path,
        checksum="1111111111222222222233333333334444444444555555555566666666667777",
    )
    db.commit()

    # Mock storage to return corrupt PDF bytes
    from app.storage.storage_service import storage_service

    monkeypatch.setattr(storage_service, "get_file", lambda path: b"Not a PDF")

    with pytest.raises(Exception):
        DocumentParsingService.process_document(db, doc_id)

    db.refresh(doc)
    assert doc.status == DocumentStatus.FAILED.value

    parsed = parsed_repo.get_parsed_document(db, doc_id)
    assert parsed is not None
    assert parsed.status == ParsedDocumentStatus.FAILED.value


# ──────────────────────────────────────────────────────────────────────────────
# 5. API Tests — GET /documents/{id}/parsed
# ──────────────────────────────────────────────────────────────────────────────

def test_api_get_parsed_document_success(client, db, mock_user):
    doc_id = str(uuid.uuid4())
    doc = doc_repo.create_document(
        db,
        id=doc_id,
        user_id=mock_user.id,
        original_filename="guide.md",
        stored_filename=f"{doc_id}.md",
        display_name="guide",
        file_extension="md",
        mime_type="text/markdown",
        file_size=30,
        storage_path=f"{mock_user.id}/{doc_id}.md",
        checksum="9999999999888888888877777777776666666666555555555544444444443333",
        status=DocumentStatus.READY.value,
    )
    parsed_repo.create_parsed_document(
        db,
        document_id=doc_id,
        text_content="Extracted Markdown Guide",
        status=ParsedDocumentStatus.READY.value,
    )
    db.commit()

    res = client.get(f"/documents/{doc_id}/parsed")
    assert res.status_code == 200
    data = res.json()
    assert data["document_id"] == doc_id
    assert data["status"] == "READY"
    assert data["text_content"] == "Extracted Markdown Guide"
    assert data["char_count"] == len("Extracted Markdown Guide")


def test_api_get_parsed_document_not_found(client, db, mock_user):
    doc_id = str(uuid.uuid4())
    doc_repo.create_document(
        db,
        id=doc_id,
        user_id=mock_user.id,
        original_filename="unparsed.txt",
        stored_filename=f"{doc_id}.txt",
        display_name="unparsed",
        file_extension="txt",
        mime_type="text/plain",
        file_size=10,
        storage_path=f"{mock_user.id}/{doc_id}.txt",
        checksum="0000000000111111111122222222223333333333444444444455555555556666",
        status=DocumentStatus.UPLOADED.value,
    )
    db.commit()

    res = client.get(f"/documents/{doc_id}/parsed")
    assert res.status_code == 404
    assert "not been parsed yet" in res.json()["detail"]


def test_api_get_parsed_document_cross_user_forbidden(
    client, db, mock_user, mock_other_user
):
    doc_id = str(uuid.uuid4())
    # Created by mock_other_user (id=102)
    doc_repo.create_document(
        db,
        id=doc_id,
        user_id=mock_other_user.id,
        original_filename="private.txt",
        stored_filename=f"{doc_id}.txt",
        display_name="private",
        file_extension="txt",
        mime_type="text/plain",
        file_size=15,
        storage_path=f"{mock_other_user.id}/{doc_id}.txt",
        checksum="7777777777888888888899999999990000000000111111111122222222223333",
        status=DocumentStatus.READY.value,
    )
    parsed_repo.create_parsed_document(
        db,
        document_id=doc_id,
        text_content="Top Secret Text",
        status=ParsedDocumentStatus.READY.value,
    )
    db.commit()

    # client is authenticated as mock_user (id=101)
    res = client.get(f"/documents/{doc_id}/parsed")
    assert res.status_code == 403
    assert "permission" in res.json()["detail"].lower()
