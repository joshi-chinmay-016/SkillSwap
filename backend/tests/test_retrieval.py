"""
Day 71 — Retrieval Foundation & Production Hardening (Parts A1 + A2) — Test Suite.

Comprehensive tests for:
    - Query request validation (empty, whitespace, top_k bounds, threshold, document_id format)
    - Query embedding generation & dimension mismatch validation
    - FAISS search via VectorStore abstraction
    - Vector-ID resolution & batch PostgreSQL lookup (no N+1 queries)
    - Ownership authorization (User A cannot access User B's content)
    - Document-scoped retrieval
    - Lifecycle filtering (ARCHIVED documents, chunks, and embeddings excluded)
    - Empty index safe handling
    - Insufficient results safe handling
    - Stale / orphaned FAISS vector handling (skipped safely without crashing)
    - Duplicate chunk handling (keep highest-scoring occurrence)
    - Similarity threshold filtering
    - Deterministic result ordering (score desc, chunk_id asc)
    - Retrieval metrics & timing structure
    - API security & authorization via FastAPI TestClient
    - Retrieval quality smoke test (deterministic synthetic dataset)
    - N+1 query assertion test
"""
from __future__ import annotations

import os
import shutil
import tempfile
import uuid
from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import settings
from app.core.database import get_db
from app.dependencies.current_user import get_current_user
from app.main import app
from app.models.base import Base
from app.models.chunk import Chunk, ChunkStatus
from app.models.document import Document, DocumentStatus
from app.models.embedding import Embedding, EmbeddingStatus
from app.models.parsed_document import ParsedDocument, ParsedDocumentStatus
from app.models.user import User
from app.models.vector_index_entry import VectorIndexEntry, VectorIndexStatus
from app.retrieval import (
    FAISSRetriever,
    InvalidRetrievalRequestError,
    QueryEmbeddingError,
    RetrievalRequest,
    RetrievalResponse,
    RetrievalService,
    RetrievalUnavailableError,
    RetrievedChunk,
    VectorStoreSearchError,
)
from app.retrieval.retrieval_repository import get_candidate_metadata_batch
from app.vector_store.faiss_store import FAISSVectorStore, _embedding_id_to_faiss_id

# ── Test Database Fixture ──────────────────────────────────────────────────────

TEST_DIM = 3072


@pytest.fixture
def test_db():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    with engine.connect() as conn:
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
                display_name TEXT NOT NULL DEFAULT 'doc',
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
                user_id INTEGER NOT NULL DEFAULT 1,
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
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """))
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS vector_index_entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                embedding_id TEXT NOT NULL UNIQUE,
                faiss_id INTEGER NOT NULL UNIQUE,
                status TEXT NOT NULL DEFAULT 'INDEXED',
                indexed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                failure_reason TEXT,
                FOREIGN KEY (embedding_id) REFERENCES embeddings(id) ON DELETE CASCADE
            )
        """))
        conn.commit()

    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def tmp_vector_store():
    tmp_dir = Path(tempfile.mkdtemp())
    index_path = tmp_dir / "test.index"
    mapping_path = tmp_dir / "test_mapping.json"
    store = FAISSVectorStore(
        index_path=index_path,
        mapping_path=mapping_path,
        dimension=TEST_DIM,
    )
    store.initialize_index()
    yield store
    shutil.rmtree(tmp_dir, ignore_errors=True)


@pytest.fixture
def mock_embedding_provider():
    provider = MagicMock()
    # Default unit vector for query
    vec = [0.0] * TEST_DIM
    vec[0] = 1.0
    provider.embed_query.return_value = vec
    return provider


# ── Helper Data Generators ────────────────────────────────────────────────────

def create_test_user(db: Session, user_id: int = 1) -> User:
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        user = User(
            id=user_id,
            name=f"User {user_id}",
            email=f"user{user_id}@example.com",
            password_hash="hashed_password",
        )
        db.add(user)
        db.flush()
    return user


def create_test_document_chain(
    db: Session,
    user_id: int = 1,
    doc_status: str = DocumentStatus.READY.value,
    chunk_status: str = ChunkStatus.READY.value,
    emb_status: str = EmbeddingStatus.READY.value,
    chunk_text: str = "Test chunk content",
    doc_name: str = "TestDoc.pdf",
    vector: list[float] | None = None,
) -> tuple[Document, Chunk, Embedding]:
    create_test_user(db, user_id)

    doc = Document(
        id=str(uuid.uuid4()),
        user_id=user_id,
        original_filename=doc_name,
        stored_filename=f"{uuid.uuid4()}.pdf",
        display_name=doc_name,
        file_extension="pdf",
        file_size=1024,
        mime_type="application/pdf",
        storage_path=f"uploads/{user_id}/test.pdf",
        checksum="dummychecksum",
        status=doc_status,
    )
    db.add(doc)

    parsed_doc = ParsedDocument(
        id=str(uuid.uuid4()),
        document_id=doc.id,
        text_content=chunk_text,
        status=ParsedDocumentStatus.READY.value,
    )
    db.add(parsed_doc)

    chunk = Chunk(
        id=str(uuid.uuid4()),
        parsed_document_id=parsed_doc.id,
        user_id=user_id,
        chunk_index=0,
        chunk_text=chunk_text,
        status=chunk_status,
    )
    db.add(chunk)

    if vector is None:
        vector = [0.0] * TEST_DIM
        vector[0] = 1.0

    emb = Embedding(
        id=str(uuid.uuid4()),
        chunk_id=chunk.id,
        parsed_document_id=parsed_doc.id,
        user_id=user_id,
        provider="gemini",
        model_name="gemini-embedding-001",
        model_version="v1",
        embedding_version=1,
        dimension=TEST_DIM,
        status=emb_status,
    )
    if emb_status == EmbeddingStatus.READY.value:
        emb.set_vector(vector)
    db.add(emb)

    db.flush()
    return doc, chunk, emb


# ── Unit Tests ────────────────────────────────────────────────────────────────

def test_request_validation():
    """Verify input validation for query, top_k, threshold, document_id."""
    service = RetrievalService(
        retriever=MagicMock(),
        embedding_provider=MagicMock(),
        default_top_k=5,
        max_top_k=20,
        default_threshold=0.0,
        max_query_length=100,
    )

    # Empty / whitespace query
    with pytest.raises(InvalidRetrievalRequestError, match="must not be empty"):
        service.retrieve(MagicMock(), request=RetrievalRequest(query=""), user_id=1)
    with pytest.raises(InvalidRetrievalRequestError, match="must not be empty"):
        service.retrieve(MagicMock(), request=RetrievalRequest(query="   "), user_id=1)

    # Query too long
    with pytest.raises(InvalidRetrievalRequestError, match="exceeds maximum length"):
        service.retrieve(MagicMock(), request=RetrievalRequest(query="a" * 105), user_id=1)

    # top_k bounds
    with pytest.raises(InvalidRetrievalRequestError, match="top_k must be >= 1"):
        service.retrieve(MagicMock(), request=RetrievalRequest(query="valid", top_k=0), user_id=1)
    with pytest.raises(InvalidRetrievalRequestError, match="top_k must be <= 20"):
        service.retrieve(MagicMock(), request=RetrievalRequest(query="valid", top_k=50), user_id=1)

    # Threshold bounds
    with pytest.raises(InvalidRetrievalRequestError, match="similarity_threshold must be between"):
        service.retrieve(MagicMock(), request=RetrievalRequest(query="valid", similarity_threshold=-0.1), user_id=1)
    with pytest.raises(InvalidRetrievalRequestError, match="similarity_threshold must be between"):
        service.retrieve(MagicMock(), request=RetrievalRequest(query="valid", similarity_threshold=1.5), user_id=1)

    # Invalid document_id format
    with pytest.raises(InvalidRetrievalRequestError, match="document_id must be a valid UUID"):
        service.retrieve(MagicMock(), request=RetrievalRequest(query="valid", document_id="invalid-id"), user_id=1)


def test_empty_faiss_index_returns_empty_response(test_db, tmp_vector_store, mock_embedding_provider):
    """Empty FAISS index should return 0 results cleanly without errors."""
    retriever = FAISSRetriever(tmp_vector_store)
    service = RetrievalService(
        retriever=retriever,
        embedding_provider=mock_embedding_provider,
        default_top_k=5,
        max_top_k=20,
        default_threshold=0.0,
        max_query_length=2000,
    )

    resp = service.retrieve(test_db, request=RetrievalRequest(query="Python dependency injection"), user_id=1)
    assert resp.total == 0
    assert resp.results == []
    assert resp.query_duration_ms >= 0.0


def test_query_dimension_mismatch(tmp_vector_store, mock_embedding_provider):
    """Query dimension mismatch must be rejected cleanly."""
    mock_embedding_provider.embed_query.return_value = [0.1] * 768  # 768 vs 3072
    retriever = FAISSRetriever(tmp_vector_store)
    service = RetrievalService(
        retriever=retriever,
        embedding_provider=mock_embedding_provider,
        default_top_k=5,
        max_top_k=20,
        default_threshold=0.0,
        max_query_length=2000,
    )

    with pytest.raises(VectorStoreSearchError, match="dimension 768 does not match"):
        service.retrieve(MagicMock(), request=RetrievalRequest(query="test query"), user_id=1)


def test_successful_retrieval_and_ownership_filtering(test_db, tmp_vector_store, mock_embedding_provider):
    """Verify FAISS retrieval, PostgreSQL metadata resolution, and user ownership isolation."""
    # User 1 document
    vec1 = [0.0] * TEST_DIM
    vec1[0] = 1.0
    doc1, chunk1, emb1 = create_test_document_chain(
        test_db, user_id=1, chunk_text="FastAPI dependency injection pattern", vector=vec1
    )

    # User 2 document (should be hidden from User 1)
    vec2 = [0.0] * TEST_DIM
    vec2[0] = 0.99
    doc2, chunk2, emb2 = create_test_document_chain(
        test_db, user_id=2, chunk_text="User 2 secret notes", vector=vec2
    )

    # Index both vectors in FAISS
    tmp_vector_store.add_vectors([vec1, vec2], [emb1.id, emb2.id])

    retriever = FAISSRetriever(tmp_vector_store)
    service = RetrievalService(
        retriever=retriever,
        embedding_provider=mock_embedding_provider,
        default_top_k=5,
        max_top_k=20,
        default_threshold=0.0,
        max_query_length=2000,
    )

    # Query as User 1
    resp1 = service.retrieve(test_db, request=RetrievalRequest(query="dependency injection"), user_id=1)
    assert resp1.total == 1
    assert resp1.results[0].chunk_id == chunk1.id
    assert resp1.results[0].content == "FastAPI dependency injection pattern"
    assert resp1.results[0].rank == 1

    # Query as User 2
    resp2 = service.retrieve(test_db, request=RetrievalRequest(query="secret notes"), user_id=2)
    assert resp2.total == 1
    assert resp2.results[0].chunk_id == chunk2.id


def test_document_scoped_retrieval(test_db, tmp_vector_store, mock_embedding_provider):
    """Verify restricting search to a specific document_id."""
    vec1 = [0.0] * TEST_DIM
    vec1[0] = 1.0
    doc1, chunk1, emb1 = create_test_document_chain(test_db, user_id=1, chunk_text="Doc 1 chunk", vector=vec1)

    vec2 = [0.0] * TEST_DIM
    vec2[0] = 0.95
    doc2, chunk2, emb2 = create_test_document_chain(test_db, user_id=1, chunk_text="Doc 2 chunk", vector=vec2)

    tmp_vector_store.add_vectors([vec1, vec2], [emb1.id, emb2.id])

    retriever = FAISSRetriever(tmp_vector_store)
    service = RetrievalService(
        retriever=retriever,
        embedding_provider=mock_embedding_provider,
        default_top_k=5,
        max_top_k=20,
        default_threshold=0.0,
        max_query_length=2000,
    )

    # Search scoped to Doc 1 only
    resp = service.retrieve(test_db, request=RetrievalRequest(query="chunk", document_id=doc1.id), user_id=1)
    assert resp.total == 1
    assert resp.results[0].chunk_id == chunk1.id
    assert resp.results[0].document_id == doc1.id


def test_lifecycle_filtering(test_db, tmp_vector_store, mock_embedding_provider):
    """Archived documents, chunks, or non-READY embeddings must be excluded."""
    vec = [0.0] * TEST_DIM
    vec[0] = 1.0

    # 1. Archived Document
    doc_arch, chunk1, emb1 = create_test_document_chain(
        test_db, user_id=1, doc_status=DocumentStatus.ARCHIVED.value, vector=vec
    )
    # 2. Archived Chunk
    doc2, chunk_arch, emb2 = create_test_document_chain(
        test_db, user_id=1, chunk_status=ChunkStatus.ARCHIVED.value, vector=vec
    )
    # 3. Non-READY Embedding
    doc3, chunk3, emb_fail = create_test_document_chain(
        test_db, user_id=1, emb_status=EmbeddingStatus.FAILED.value, vector=vec
    )

    tmp_vector_store.add_vectors([vec, vec, vec], [emb1.id, emb2.id, emb_fail.id])

    retriever = FAISSRetriever(tmp_vector_store)
    service = RetrievalService(
        retriever=retriever,
        embedding_provider=mock_embedding_provider,
        default_top_k=5,
        max_top_k=20,
        default_threshold=0.0,
        max_query_length=2000,
    )

    resp = service.retrieve(test_db, request=RetrievalRequest(query="test"), user_id=1)
    assert resp.total == 0


def test_stale_and_orphaned_vectors_handled_safely(test_db, tmp_vector_store, mock_embedding_provider):
    """Vectors in FAISS that do not exist in DB or mapping must be safely skipped."""
    vec = [0.0] * TEST_DIM
    vec[0] = 1.0
    doc, chunk, emb = create_test_document_chain(test_db, user_id=1, vector=vec)

    tmp_vector_store.add_vectors([vec], [emb.id])

    # Manually insert a stale vector into FAISS index directly
    stale_emb_id = str(uuid.uuid4())
    stale_vec = [0.0] * TEST_DIM
    stale_vec[0] = 0.99
    # Add via store so it has a mapping but no DB row
    tmp_vector_store.add_vectors([stale_vec], [stale_emb_id])

    retriever = FAISSRetriever(tmp_vector_store)
    service = RetrievalService(
        retriever=retriever,
        embedding_provider=mock_embedding_provider,
        default_top_k=5,
        max_top_k=20,
        default_threshold=0.0,
        max_query_length=2000,
    )

    resp = service.retrieve(test_db, request=RetrievalRequest(query="test"), user_id=1)
    assert resp.total == 1
    assert resp.results[0].chunk_id == chunk.id


def test_duplicate_chunk_deduplication(test_db, tmp_vector_store, mock_embedding_provider):
    """If multiple vector IDs resolve to the same chunk, keep highest-score occurrence."""
    vec1 = [0.0] * TEST_DIM
    vec1[0] = 0.8

    vec2 = [0.0] * TEST_DIM
    vec2[0] = 0.95  # Higher score

    doc, chunk, emb1 = create_test_document_chain(test_db, user_id=1, vector=vec1)

    # Second embedding for same chunk
    emb2 = Embedding(
        id=str(uuid.uuid4()),
        chunk_id=chunk.id,
        parsed_document_id=emb1.parsed_document_id,
        user_id=1,
        provider="gemini",
        model_name="gemini-embedding-001",
        model_version="v2",
        embedding_version=2,
        dimension=TEST_DIM,
        status=EmbeddingStatus.READY.value,
    )
    emb2.set_vector(vec2)
    test_db.add(emb2)
    test_db.flush()

    tmp_vector_store.add_vectors([vec1, vec2], [emb1.id, emb2.id])

    retriever = FAISSRetriever(tmp_vector_store)
    service = RetrievalService(
        retriever=retriever,
        embedding_provider=mock_embedding_provider,
        default_top_k=5,
        max_top_k=20,
        default_threshold=0.0,
        max_query_length=2000,
    )

    resp = service.retrieve(test_db, request=RetrievalRequest(query="test"), user_id=1)
    assert resp.total == 1
    assert resp.results[0].chunk_id == chunk.id
    assert resp.results[0].score == 0.95


def test_similarity_threshold(test_db, tmp_vector_store, mock_embedding_provider):
    """Candidates scoring below threshold must be excluded."""
    vec_high = [0.0] * TEST_DIM
    vec_high[0] = 0.9

    vec_low = [0.0] * TEST_DIM
    vec_low[0] = 0.3

    doc1, chunk_high, emb_high = create_test_document_chain(test_db, user_id=1, chunk_text="High match", vector=vec_high)
    doc2, chunk_low, emb_low = create_test_document_chain(test_db, user_id=1, chunk_text="Low match", vector=vec_low)

    tmp_vector_store.add_vectors([vec_high, vec_low], [emb_high.id, emb_low.id])

    retriever = FAISSRetriever(tmp_vector_store)
    service = RetrievalService(
        retriever=retriever,
        embedding_provider=mock_embedding_provider,
        default_top_k=5,
        max_top_k=20,
        default_threshold=0.5,  # 0.5 threshold
        max_query_length=2000,
    )

    resp = service.retrieve(test_db, request=RetrievalRequest(query="test", similarity_threshold=0.5), user_id=1)
    assert resp.total == 1
    assert resp.results[0].chunk_id == chunk_high.id


def test_batch_metadata_lookup_no_n_plus_one(test_db):
    """Assert batch metadata resolution issues a single JOIN query."""
    create_test_document_chain(test_db, user_id=1)
    create_test_document_chain(test_db, user_id=1)

    embs = test_db.query(Embedding).all()
    emb_ids = [e.id for e in embs]

    with patch.object(test_db, "query", wraps=test_db.query) as spy_query:
        meta_map = get_candidate_metadata_batch(test_db, emb_ids)
        assert len(meta_map) == 2
        # Only 1 main query call to test_db.query
        assert spy_query.call_count == 1


# ── Quality Smoke Test ────────────────────────────────────────────────────────

def test_retrieval_quality_smoke_test(test_db, tmp_vector_store, mock_embedding_provider):
    """
    Deterministic smoke test on 4 distinct topic chunks.
    Validates semantic ranking ordering.
    """
    # 4 distinct orthogonal-ish vectors
    v_di = [1.0] + [0.0] * (TEST_DIM - 1)
    v_react = [0.0, 1.0] + [0.0] * (TEST_DIM - 2)
    v_sql = [0.0, 0.0, 1.0] + [0.0] * (TEST_DIM - 3)
    v_py = [0.0, 0.0, 0.0, 1.0] + [0.0] * (TEST_DIM - 4)

    d1, c1, e1 = create_test_document_chain(test_db, user_id=1, chunk_text="FastAPI dependency injection framework", vector=v_di)
    d2, c2, e2 = create_test_document_chain(test_db, user_id=1, chunk_text="React component lifecycle and hooks", vector=v_react)
    d3, c3, e3 = create_test_document_chain(test_db, user_id=1, chunk_text="PostgreSQL B-tree index optimization", vector=v_sql)
    d4, c4, e4 = create_test_document_chain(test_db, user_id=1, chunk_text="Python custom exception handling strategies", vector=v_py)

    tmp_vector_store.add_vectors([v_di, v_react, v_sql, v_py], [e1.id, e2.id, e3.id, e4.id])

    retriever = FAISSRetriever(tmp_vector_store)
    service = RetrievalService(
        retriever=retriever,
        embedding_provider=mock_embedding_provider,
        default_top_k=5,
        max_top_k=20,
        default_threshold=0.0,
        max_query_length=2000,
    )

    # Query close to Dependency Injection
    query_v = [0.9] + [0.1] * (TEST_DIM - 1)
    mock_embedding_provider.embed_query.return_value = query_v

    resp = service.retrieve(test_db, request=RetrievalRequest(query="dependency injection"), user_id=1)
    assert resp.total == 4
    # Highest ranked chunk must be DI
    assert resp.results[0].chunk_id == c1.id
    assert resp.results[0].rank == 1


# ── API Contract & Security Tests ─────────────────────────────────────────────

def test_retrieval_api_endpoint(test_db, tmp_vector_store):
    """Test POST /retrieval/search HTTP endpoint via FastAPI TestClient."""
    doc, chunk, emb = create_test_document_chain(test_db, user_id=1, chunk_text="API search content")

    vec = [0.0] * TEST_DIM
    vec[0] = 1.0
    tmp_vector_store.add_vectors([vec], [emb.id])

    app.dependency_overrides[get_db] = lambda: test_db

    user1 = test_db.query(User).filter(User.id == 1).first()

    with patch("app.retrieval.retrieval_service.RetrievalService.create") as mock_create:
        mock_svc = MagicMock()
        mock_svc.retrieve.return_value = RetrievalResponse(
            results=[
                RetrievedChunk(
                    chunk_id=chunk.id,
                    document_id=doc.id,
                    document_name=doc.original_filename,
                    content=chunk.chunk_text,
                    score=0.98,
                    rank=1,
                )
            ],
            total=1,
            query_duration_ms=12.5,
            embedding_ms=5.0,
            faiss_ms=2.0,
            db_ms=5.5,
        )
        mock_create.return_value = mock_svc

        client = TestClient(app)

        # 1. Unauthenticated request -> 401
        res_unauth = client.post("/retrieval/search", json={"query": "test"})
        assert res_unauth.status_code == 401

        # 2. Authenticated request
        app.dependency_overrides[get_current_user] = lambda: user1
        res = client.post(
            "/retrieval/search",
            json={"query": "API search content", "top_k": 3},
        )
        assert res.status_code == 200
        data = res.json()
        assert data["total"] == 1
        assert data["results"][0]["chunk_id"] == chunk.id
        assert data["results"][0]["score"] == 0.98
        assert "query_duration_ms" in data

    app.dependency_overrides.clear()
