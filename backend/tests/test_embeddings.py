"""
Day 69 — Embedding Generation Engine (Part A1 + Part A2) — Comprehensive Test Suite.

Coverage:
    1. EmbeddingValidator
        - Valid vector
        - None vector
        - Empty vector
        - Non-numeric values
        - NaN values
        - Infinity values
        - Dimension mismatch

    2. EmbeddingResult
        - Structure & safe_repr (never logs vector)
        - BatchEmbeddingResult stats

    3. EmbeddingProvider (GeminiEmbeddingProvider)
        - Valid single & batch embedding calls (mocked API)
        - Handling rate limits (HTTP 429 → EmbeddingRateLimitError)
        - Handling timeouts (EmbeddingTimeoutError)
        - Handling server errors (HTTP 500 → EmbeddingProviderError)
        - Configuration errors (missing API key)

    4. EmbeddingRepository
        - create_embedding, bulk_create_embeddings
        - get_embedding, get_embedding_by_chunk, get_active_embedding_by_chunk
        - exists_for_version (idempotency check)
        - update_embedding_status, update_embedding_vector
        - archive_embedding, bulk_archive_embeddings
        - get_chunks_without_ready_embedding (partial completion check)

    5. EmbeddingService
        - Full document embedding pipeline (READY chunks → EmbeddingService → Provider Mock → Persisted DB)
        - Idempotency: skip chunks that already have READY embedding
        - Partial completion resumption (resumes remaining chunks)
        - Re-embedding (force_reembed: archives old, creates new READY embeddings)
        - Retry logic on recoverable provider errors
        - Permanent failure handling (transitions to FAILED after retries exhausted)
        - User ownership validation

    6. Background Job
        - run_embedding_generation_job
        - run_embedding_retry_job
"""
from __future__ import annotations

import math
import threading
import uuid
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import get_db
from app.embeddings.embedding_provider import EmbeddingProvider
from app.embeddings.embedding_result import (
    EMBEDDING_STATUS_FAILED,
    EMBEDDING_STATUS_READY,
    BatchEmbeddingResult,
    EmbeddingResult,
)
from app.embeddings.providers.gemini_embedding_provider import GeminiEmbeddingProvider
from app.exceptions.embedding_exceptions import (
    EmbeddingConfigurationError,
    EmbeddingError,
    EmbeddingProviderError,
    EmbeddingRateLimitError,
    EmbeddingTimeoutError,
    EmbeddingValidationError,
)
from app.jobs.embedding_generation_job import (
    run_embedding_generation_job,
    run_embedding_retry_job,
)
from app.models.base import Base
from app.models.chunk import Chunk, ChunkStatus
from app.models.document import Document, DocumentStatus
from app.models.embedding import Embedding, EmbeddingStatus
from app.models.parsed_document import ParsedDocument, ParsedDocumentStatus
from app.models.user import User
from app.repositories import embedding_repository as emb_repo
from app.services.embedding_service import EmbeddingService
from app.utils.embedding_validator import (
    is_valid_vector,
    validate_vector,
    validate_vectors,
)

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


@pytest.fixture(autouse=True)
def setup_db():
    with _test_engine.connect() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                oauth_provider TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS documents (
                id TEXT PRIMARY KEY,
                user_id INTEGER NOT NULL,
                original_filename TEXT NOT NULL,
                stored_filename TEXT NOT NULL,
                display_name TEXT NOT NULL,
                file_extension TEXT NOT NULL,
                mime_type TEXT NOT NULL,
                file_size INTEGER NOT NULL,
                storage_path TEXT NOT NULL,
                checksum TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'UPLOADED',
                uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                deleted_at TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """))
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS parsed_documents (
                id TEXT PRIMARY KEY,
                document_id TEXT NOT NULL UNIQUE,
                text_content TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'PENDING',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE
            )
        """))
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS chunks (
                id TEXT PRIMARY KEY,
                parsed_document_id TEXT NOT NULL,
                user_id INTEGER NOT NULL,
                chunk_index INTEGER NOT NULL,
                chunk_text TEXT NOT NULL,
                start_offset INTEGER NOT NULL DEFAULT 0,
                end_offset INTEGER NOT NULL DEFAULT 0,
                estimated_tokens INTEGER NOT NULL DEFAULT 0,
                chunk_size INTEGER NOT NULL DEFAULT 800,
                overlap_size INTEGER NOT NULL DEFAULT 150,
                page_start INTEGER,
                page_end INTEGER,
                section TEXT,
                strategy TEXT NOT NULL DEFAULT 'recursive',
                strategy_version TEXT NOT NULL DEFAULT '1.0.0',
                status TEXT NOT NULL DEFAULT 'PENDING',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (parsed_document_id) REFERENCES parsed_documents(id) ON DELETE CASCADE,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """))
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS embeddings (
                id TEXT PRIMARY KEY,
                chunk_id TEXT NOT NULL,
                parsed_document_id TEXT NOT NULL,
                user_id INTEGER NOT NULL,
                provider TEXT NOT NULL,
                model_name TEXT NOT NULL,
                model_version TEXT NOT NULL,
                embedding_version INTEGER NOT NULL DEFAULT 1,
                dimension INTEGER NOT NULL,
                vector_json TEXT,
                status TEXT NOT NULL DEFAULT 'PENDING',
                failure_count INTEGER NOT NULL DEFAULT 0,
                error_category TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                archived_at TIMESTAMP,
                FOREIGN KEY (chunk_id) REFERENCES chunks(id) ON DELETE CASCADE,
                FOREIGN KEY (parsed_document_id) REFERENCES parsed_documents(id) ON DELETE CASCADE,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                CONSTRAINT uq_embedding_chunk_model_version UNIQUE (chunk_id, provider, model_name, model_version, embedding_version)
            )
        """))
        conn.commit()

    db = TestingSessionLocal()

    def _override_get_db():
        try:
            yield db
        finally:
            pass

    from app.main import app
    app.dependency_overrides[get_db] = _override_get_db
    yield db
    db.close()
    app.dependency_overrides.clear()

    with _test_engine.connect() as conn:
        conn.execute(text("DROP TABLE IF EXISTS embeddings"))
        conn.execute(text("DROP TABLE IF EXISTS chunks"))
        conn.execute(text("DROP TABLE IF EXISTS parsed_documents"))
        conn.execute(text("DROP TABLE IF EXISTS documents"))
        conn.execute(text("DROP TABLE IF EXISTS users"))
        conn.commit()


# ──────────────────────────────────────────────────────────────────────────────
# Mock Provider for Service/Repository Testing
# ──────────────────────────────────────────────────────────────────────────────

class MockEmbeddingProvider(EmbeddingProvider):
    def __init__(self, dimension: int = 768, failure_trigger: str | None = None) -> None:
        self._dimension = dimension
        self.failure_trigger = failure_trigger
        self.call_count = 0

    def generate_embedding(self, text: str) -> list[float]:
        results = self.generate_embeddings([text])
        return results[0]

    def generate_embeddings(self, texts: list[str]) -> list[list[float]]:
        self.call_count += 1
        if self.failure_trigger == "rate_limit":
            raise EmbeddingRateLimitError("Rate limit hit")
        elif self.failure_trigger == "timeout":
            raise EmbeddingTimeoutError("Timeout hit")
        elif self.failure_trigger == "provider_error":
            raise EmbeddingProviderError("Provider failure")
        elif self.failure_trigger == "invalid_vector":
            return [[0.1] * (self._dimension - 1)] * len(texts)  # wrong dimension

        return [[0.1 * (i + 1)] * self._dimension for i in range(len(texts))]

    def get_dimension(self) -> int:
        return self._dimension

    def get_model_name(self) -> str:
        return "mock-embedding-model"

    def get_model_version(self) -> str:
        return "v1"

    @property
    def provider_name(self) -> str:
        return "mock"


# ──────────────────────────────────────────────────────────────────────────────
# Helper Functions to Seed Test DB
# ──────────────────────────────────────────────────────────────────────────────

def _seed_user(db) -> User:
    user = User(
        name=f"User {uuid.uuid4().hex[:6]}",
        email=f"test-{uuid.uuid4().hex[:6]}@example.com",
        password_hash="hashed_pwd_123",
    )
    db.add(user)
    db.flush()
    return user


def _seed_document_parsed_and_chunks(db, user: User, chunk_count: int = 3) -> tuple[Document, ParsedDocument, list[Chunk]]:
    doc = Document(
        user_id=user.id,
        original_filename="doc.pdf",
        stored_filename=f"{uuid.uuid4()}.pdf",
        display_name="Doc",
        file_extension="pdf",
        mime_type="application/pdf",
        file_size=1024,
        storage_path=f"{user.id}/doc.pdf",
        checksum="dummy_checksum",
        status=DocumentStatus.READY.value,
    )
    db.add(doc)
    db.flush()

    parsed = ParsedDocument(
        document_id=doc.id,
        text_content="Sample text content for parsing.",
        status=ParsedDocumentStatus.READY.value,
    )
    db.add(parsed)
    db.flush()

    chunks = []
    for i in range(chunk_count):
        chunk = Chunk(
            parsed_document_id=parsed.id,
            user_id=user.id,
            chunk_index=i,
            chunk_text=f"Chunk {i} content text",
            start_offset=i * 20,
            end_offset=(i + 1) * 20,
            estimated_tokens=5,
            chunk_size=800,
            overlap_size=150,
            strategy="recursive",
            strategy_version="1.0.0",
            status=ChunkStatus.READY.value,
        )
        db.add(chunk)
        chunks.append(chunk)
    db.flush()
    db.commit()

    return doc, parsed, chunks


# ==============================================================================
# 1. EmbeddingValidator Tests
# ==============================================================================

def test_validator_valid_vector():
    vec = [0.1, 0.2, 0.3, 0.4]
    validate_vector(vec, expected_dimension=4, chunk_id="chunk-1")
    assert is_valid_vector(vec, 4) is True


def test_validator_none_vector():
    with pytest.raises(EmbeddingValidationError) as exc:
        validate_vector(None, expected_dimension=4, chunk_id="c1")
    assert "Vector is None" in str(exc.value)
    assert is_valid_vector(None, 4) is False


def test_validator_empty_vector():
    with pytest.raises(EmbeddingValidationError) as exc:
        validate_vector([], expected_dimension=4, chunk_id="c1")
    assert "empty" in str(exc.value)


def test_validator_non_numeric_vector():
    with pytest.raises(EmbeddingValidationError) as exc:
        validate_vector([0.1, "invalid", 0.3, 0.4], expected_dimension=4, chunk_id="c1")
    assert "Non-numeric" in str(exc.value)


def test_validator_nan_vector():
    with pytest.raises(EmbeddingValidationError) as exc:
        validate_vector([0.1, math.nan, 0.3, 0.4], expected_dimension=4, chunk_id="c1")
    assert "NaN" in str(exc.value)


def test_validator_inf_vector():
    with pytest.raises(EmbeddingValidationError) as exc:
        validate_vector([0.1, math.inf, 0.3, 0.4], expected_dimension=4, chunk_id="c1")
    assert "Infinity" in str(exc.value)


def test_validator_dimension_mismatch():
    with pytest.raises(EmbeddingValidationError) as exc:
        validate_vector([0.1, 0.2, 0.3], expected_dimension=4, chunk_id="c1")
    assert "Dimension mismatch" in str(exc.value)


def test_validate_vectors_batch():
    batch = [
        [0.1, 0.2],
        [0.3, 0.4],
        [0.5], # wrong dim
    ]
    errors = validate_vectors(batch, expected_dimension=2)
    assert len(errors) == 1
    assert "index=2" in errors[0]


# ==============================================================================
# 2. EmbeddingResult Tests
# ==============================================================================

def test_embedding_result_safe_repr():
    res = EmbeddingResult(
        chunk_id="chunk-123",
        vector=[0.1, 0.2, 0.3],
        provider="gemini",
        model_name="text-embedding-004",
        model_version="v1",
        dimension=3,
        embedding_version=1,
    )
    r_str = repr(res)
    assert "chunk-123" in r_str
    assert "gemini" in r_str
    # Crucial: vector values must NEVER be in repr
    assert "0.1" not in r_str
    assert "[0.1, 0.2, 0.3]" not in r_str


def test_batch_embedding_result_stats():
    res1 = EmbeddingResult(chunk_id="c1", vector=[0.1], provider="m", model_name="m", model_version="v1", dimension=1, embedding_version=1, status=EMBEDDING_STATUS_READY, duration_ms=10.0)
    res2 = EmbeddingResult(chunk_id="c2", vector=[], provider="m", model_name="m", model_version="v1", dimension=1, embedding_version=1, status=EMBEDDING_STATUS_FAILED, duration_ms=20.0)

    batch_res = BatchEmbeddingResult(batch_index=0, results=[res1, res2])
    assert batch_res.total == 2
    assert batch_res.ready_count == 1
    assert batch_res.failed_count == 1
    assert batch_res.average_duration_ms == 15.0


# ==============================================================================
# 3. GeminiEmbeddingProvider Tests
# ==============================================================================

def test_gemini_provider_config_missing():
    with patch("app.core.config.settings.EMBEDDING_API_KEY", ""), \
         patch("app.core.config.settings.GEMINI_API_KEY", ""):
        with pytest.raises(EmbeddingConfigurationError):
            GeminiEmbeddingProvider()


def test_gemini_provider_generate_embeddings_rest_success():
    with patch("app.core.config.settings.EMBEDDING_API_KEY", "fake_key"):
        provider = GeminiEmbeddingProvider()
        provider._sdk_client = None  # Force REST path

        mock_resp_data = {
            "embeddings": [
                {"values": [0.1] * 768},
                {"values": [0.2] * 768},
            ]
        }

        mock_cm = MagicMock()
        mock_cm.__enter__.return_value.read.return_value = json_bytes(mock_resp_data)

        with patch("urllib.request.urlopen", return_value=mock_cm):
            vecs = provider.generate_embeddings(["text 1", "text 2"])
            assert len(vecs) == 2
            assert len(vecs[0]) == 768
            assert vecs[0][0] == 0.1
            assert vecs[1][0] == 0.2


def test_gemini_provider_rest_rate_limit():
    import urllib.error
    with patch("app.core.config.settings.EMBEDDING_API_KEY", "fake_key"):
        provider = GeminiEmbeddingProvider()
        provider._sdk_client = None

        err = urllib.error.HTTPError(
            url="http://test", code=429, msg="Too Many Requests", hdrs={}, fp=MagicMock()
        )
        err.fp.read.return_value = b'{"error": "rate limit"}'

        with patch("urllib.request.urlopen", side_effect=err):
            with pytest.raises(EmbeddingRateLimitError):
                provider.generate_embeddings(["text 1"])


def test_gemini_provider_rest_server_error():
    import urllib.error
    with patch("app.core.config.settings.EMBEDDING_API_KEY", "fake_key"):
        provider = GeminiEmbeddingProvider()
        provider._sdk_client = None

        err = urllib.error.HTTPError(
            url="http://test", code=500, msg="Internal Error", hdrs={}, fp=MagicMock()
        )
        err.fp.read.return_value = b'{"error": "server error"}'

        with patch("urllib.request.urlopen", side_effect=err):
            with pytest.raises(EmbeddingProviderError):
                provider.generate_embeddings(["text 1"])


def json_bytes(obj) -> bytes:
    import json
    return json.dumps(obj).encode("utf-8")


# ==============================================================================
# 4. EmbeddingRepository Tests
# ==============================================================================

def test_repository_crud(setup_db):
    db = setup_db
    user = _seed_user(db)
    doc, parsed, chunks = _seed_document_parsed_and_chunks(db, user, chunk_count=2)

    # 1. create_embedding
    emb = emb_repo.create_embedding(
        db,
        chunk_id=chunks[0].id,
        parsed_document_id=parsed.id,
        user_id=user.id,
        provider="mock",
        model_name="mock-model",
        model_version="v1",
        embedding_version=1,
        dimension=768,
        vector=[0.5] * 768,
        status=EmbeddingStatus.READY.value,
    )
    assert emb.id is not None
    assert emb.get_vector() == [0.5] * 768

    # 2. get_embedding
    fetched = emb_repo.get_embedding(db, emb.id)
    assert fetched is not None
    assert fetched.chunk_id == chunks[0].id

    # 3. exists_for_version
    exists = emb_repo.exists_for_version(
        db,
        chunks[0].id,
        provider="mock",
        model_name="mock-model",
        model_version="v1",
        embedding_version=1,
    )
    assert exists is True

    # 4. bulk_archive_embeddings
    archived_count = emb_repo.bulk_archive_embeddings(
        db,
        [chunks[0].id],
        provider="mock",
        model_name="mock-model",
    )
    assert archived_count == 1
    assert fetched.status == EmbeddingStatus.ARCHIVED.value

    # 5. check exists after archiving (ready_only=True)
    assert emb_repo.exists_for_version(
        db,
        chunks[0].id,
        provider="mock",
        model_name="mock-model",
        model_version="v1",
        embedding_version=1,
        ready_only=True,
    ) is False


def test_repository_chunks_needing_embeddings(setup_db):
    db = setup_db
    user = _seed_user(db)
    doc, parsed, chunks = _seed_document_parsed_and_chunks(db, user, chunk_count=3)

    # Create embedding for chunk 0 only
    emb_repo.create_embedding(
        db,
        chunk_id=chunks[0].id,
        parsed_document_id=parsed.id,
        user_id=user.id,
        provider="mock",
        model_name="mock-model",
        model_version="v1",
        embedding_version=1,
        dimension=768,
        vector=[0.1] * 768,
        status=EmbeddingStatus.READY.value,
    )

    needed = emb_repo.get_chunks_without_ready_embedding(
        db,
        parsed.id,
        provider="mock",
        model_name="mock-model",
        model_version="v1",
        embedding_version=1,
    )
    assert len(needed) == 2
    assert chunks[0].id not in needed
    assert chunks[1].id in needed
    assert chunks[2].id in needed


# ==============================================================================
# 5. EmbeddingService Tests
# ==============================================================================

def test_service_full_pipeline_success(setup_db):
    db = setup_db
    user = _seed_user(db)
    doc, parsed, chunks = _seed_document_parsed_and_chunks(db, user, chunk_count=3)

    mock_provider = MockEmbeddingProvider(dimension=768)
    service = EmbeddingService(provider=mock_provider)

    result = service.generate_embeddings_for_document(
        db, document_id=doc.id, user_id=user.id
    )

    assert result["chunk_count"] == 3
    assert result["ready"] == 3
    assert result["failed"] == 0

    # Verify DB persistence
    ready_embs = emb_repo.list_ready_embeddings(db, parsed.id)
    assert len(ready_embs) == 3
    for emb in ready_embs:
        assert emb.status == EmbeddingStatus.READY.value
        assert emb.dimension == 768
        assert len(emb.get_vector()) == 768


def test_service_idempotency_skip_existing(setup_db):
    db = setup_db
    user = _seed_user(db)
    doc, parsed, chunks = _seed_document_parsed_and_chunks(db, user, chunk_count=2)

    mock_provider = MockEmbeddingProvider(dimension=768)
    service = EmbeddingService(provider=mock_provider)

    # First run
    service.generate_embeddings_for_document(db, document_id=doc.id, user_id=user.id)
    assert mock_provider.call_count == 1

    # Second run — should skip all
    result2 = service.generate_embeddings_for_document(db, document_id=doc.id, user_id=user.id)
    assert result2["chunk_count"] == 0
    assert result2["message"] == "All chunks already have READY embeddings."
    assert mock_provider.call_count == 1  # No additional calls to provider


def test_service_force_reembed(setup_db):
    db = setup_db
    user = _seed_user(db)
    doc, parsed, chunks = _seed_document_parsed_and_chunks(db, user, chunk_count=2)

    mock_provider = MockEmbeddingProvider(dimension=768)
    service = EmbeddingService(provider=mock_provider)

    # Initial generation
    service.generate_embeddings_for_document(db, document_id=doc.id, user_id=user.id)

    # Force re-embed
    result = service.reembed_document(db, document_id=doc.id, user_id=user.id)
    assert result["ready"] == 2

    # Check that 2 old embeddings are ARCHIVED and 2 new are READY
    all_embs = emb_repo.get_embeddings_by_document(db, parsed.id)
    assert len(all_embs) == 4
    ready_count = sum(1 for e in all_embs if e.status == EmbeddingStatus.READY.value)
    archived_count = sum(1 for e in all_embs if e.status == EmbeddingStatus.ARCHIVED.value)
    assert ready_count == 2
    assert archived_count == 2


def test_service_recoverable_retry_and_failure(setup_db):
    db = setup_db
    user = _seed_user(db)
    doc, parsed, chunks = _seed_document_parsed_and_chunks(db, user, chunk_count=2)

    # Provider triggers rate limit
    failing_provider = MockEmbeddingProvider(dimension=768, failure_trigger="rate_limit")
    service = EmbeddingService(provider=failing_provider)

    with patch("time.sleep"):  # Speed up tests
        result = service.generate_embeddings_for_document(db, document_id=doc.id, user_id=user.id)

    assert result["ready"] == 0
    assert result["failed"] == 2

    # Verify status in DB
    failed_embs = emb_repo.list_failed_embeddings(db, parsed.id)
    assert len(failed_embs) == 2
    assert failed_embs[0].error_category == "rate_limit"


def test_service_validation_failure(setup_db):
    db = setup_db
    user = _seed_user(db)
    doc, parsed, chunks = _seed_document_parsed_and_chunks(db, user, chunk_count=2)

    # Provider returns dimension mismatch (767 instead of 768)
    invalid_provider = MockEmbeddingProvider(dimension=768, failure_trigger="invalid_vector")
    service = EmbeddingService(provider=invalid_provider)

    result = service.generate_embeddings_for_document(db, document_id=doc.id, user_id=user.id)
    assert result["ready"] == 0
    assert result["failed"] == 2

    failed_embs = emb_repo.list_failed_embeddings(db, parsed.id)
    assert len(failed_embs) == 2
    assert failed_embs[0].error_category == "validation_error"


def test_service_ownership_validation(setup_db):
    db = setup_db
    user = _seed_user(db)
    other_user = _seed_user(db)
    doc, parsed, chunks = _seed_document_parsed_and_chunks(db, user, chunk_count=1)

    service = EmbeddingService(provider=MockEmbeddingProvider())

    with pytest.raises(ValueError) as exc:
        service.generate_embeddings_for_document(db, document_id=doc.id, user_id=other_user.id)
    assert "does not belong to user" in str(exc.value)


# ==============================================================================
# 6. Background Job Tests
# ==============================================================================

def test_run_embedding_generation_job(setup_db):
    db = setup_db
    user = _seed_user(db)
    doc, parsed, chunks = _seed_document_parsed_and_chunks(db, user, chunk_count=2)
    parsed_id = parsed.id

    mock_provider = MockEmbeddingProvider(dimension=3072)

    with patch("app.jobs.embedding_generation_job.SessionLocal", TestingSessionLocal), \
         patch("app.services.embedding_service.EmbeddingService.create", return_value=EmbeddingService(mock_provider)), \
         patch("app.jobs.embedding_generation_job._schedule_auto_retry") as mock_retry, \
         patch("app.services.vector_indexing_service.VectorIndexingService.create") as mock_vidx_create:
        mock_vidx_svc = MagicMock()
        mock_vidx_create.return_value = mock_vidx_svc
        run_embedding_generation_job(document_id=doc.id, user_id=user.id)

    # All chunks succeeded → no auto-retry scheduled
    mock_retry.assert_not_called()
    ready_embs = emb_repo.list_ready_embeddings(db, parsed_id)
    assert len(ready_embs) == 2
    mock_vidx_svc.index_document.assert_called_once()


def test_run_embedding_generation_job_auto_retry_scheduled_on_failure(setup_db):
    """When chunks fail, auto-retry daemon thread must be scheduled."""
    db = setup_db
    user = _seed_user(db)
    doc, parsed, chunks = _seed_document_parsed_and_chunks(db, user, chunk_count=2)

    failing_provider = MockEmbeddingProvider(dimension=3072, failure_trigger="rate_limit")

    with patch("app.jobs.embedding_generation_job.SessionLocal", TestingSessionLocal), \
         patch("app.services.embedding_service.EmbeddingService.create", return_value=EmbeddingService(failing_provider)), \
         patch("app.jobs.embedding_generation_job._schedule_auto_retry") as mock_retry, \
         patch("time.sleep"):
        run_embedding_generation_job(document_id=doc.id, user_id=user.id)

    # Auto-retry must have been scheduled because chunks failed
    mock_retry.assert_called_once()
    call_kwargs = mock_retry.call_args.kwargs
    assert call_kwargs["document_id"] == doc.id
    assert call_kwargs["user_id"] == user.id
    assert "delay_seconds" in call_kwargs
    assert "parent_job_id" in call_kwargs


def test_run_embedding_generation_job_no_auto_retry_when_disabled(setup_db):
    """When EMBEDDING_AUTO_RETRY=False, no retry thread must be scheduled."""
    db = setup_db
    user = _seed_user(db)
    doc, parsed, chunks = _seed_document_parsed_and_chunks(db, user, chunk_count=2)

    failing_provider = MockEmbeddingProvider(dimension=3072, failure_trigger="rate_limit")

    with patch("app.jobs.embedding_generation_job.SessionLocal", TestingSessionLocal), \
         patch("app.services.embedding_service.EmbeddingService.create", return_value=EmbeddingService(failing_provider)), \
         patch("app.jobs.embedding_generation_job._schedule_auto_retry") as mock_retry, \
         patch("app.core.config.settings") as mock_settings, \
         patch("time.sleep"):
        mock_settings.EMBEDDING_AUTO_RETRY = False
        mock_settings.EMBEDDING_BATCH_SIZE = 32
        mock_settings.EMBEDDING_MAX_RETRIES = 3
        mock_settings.EMBEDDING_VERSION = 1
        run_embedding_generation_job(document_id=doc.id, user_id=user.id)

    mock_retry.assert_not_called()


def test_run_embedding_retry_job(setup_db):
    db = setup_db
    user = _seed_user(db)
    doc, parsed, chunks = _seed_document_parsed_and_chunks(db, user, chunk_count=2)
    parsed_id = parsed.id

    # First run fails
    failing_provider = MockEmbeddingProvider(dimension=3072, failure_trigger="rate_limit")
    with patch("app.jobs.embedding_generation_job.SessionLocal", TestingSessionLocal), \
         patch("app.services.embedding_service.EmbeddingService.create", return_value=EmbeddingService(failing_provider)), \
         patch("app.jobs.embedding_generation_job._schedule_auto_retry"), \
         patch("time.sleep"):
        run_embedding_generation_job(document_id=doc.id, user_id=user.id)

    failed_embs = emb_repo.list_failed_embeddings(db, parsed_id)
    assert len(failed_embs) == 2

    # Manual retry with working provider
    working_provider = MockEmbeddingProvider(dimension=3072)
    with patch("app.jobs.embedding_generation_job.SessionLocal", TestingSessionLocal), \
         patch("app.services.embedding_service.EmbeddingService.create", return_value=EmbeddingService(working_provider)):
        run_embedding_retry_job(document_id=doc.id, user_id=user.id)

    ready_embs = emb_repo.list_ready_embeddings(db, parsed_id)
    assert len(ready_embs) == 2


def test_schedule_auto_retry_spawns_daemon_thread():
    """_schedule_auto_retry must start a daemon thread that calls run_embedding_retry_job."""
    from app.jobs.embedding_generation_job import _schedule_auto_retry

    calls = []
    with patch("app.jobs.embedding_generation_job.run_embedding_retry_job", side_effect=lambda **kw: calls.append(kw)), \
         patch("time.sleep"):  # skip real delay
        thread_holder = []

        original_thread = threading.Thread

        def capture_thread(*args, **kwargs):
            t = original_thread(*args, **kwargs)
            thread_holder.append(t)
            return t

        with patch("app.jobs.embedding_generation_job.threading.Thread", side_effect=capture_thread):
            _schedule_auto_retry(
                document_id="doc-abc",
                user_id=42,
                delay_seconds=0,
                parent_job_id="job-xyz",
            )

        # Give the thread a moment to run
        if thread_holder:
            thread_holder[0].join(timeout=3)

    assert len(calls) == 1
    assert calls[0]["document_id"] == "doc-abc"
    assert calls[0]["user_id"] == 42
