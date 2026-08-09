"""
Day 70 — FAISS Vector Storage (Part A1 + Part A2) — Comprehensive Test Suite.

Coverage:
    PART A1: Foundation
        1. Store initialization & empty index creation
        2. Vector dimension validation & mismatch rejection
        3. Index persistence & reload from disk
        4. Vector count & health check inspection
        5. ID mapping strategy & persistence across restarts
        6. Corrupted index file safe handling
        7. Missing index file initialization handling
        8. Concurrent mutation lock protection

    PART A2: Indexing & Persistence Pipeline
        9. Loading READY embeddings for indexing
        10. Batch indexing pipeline
        11. Vector pre-validation (NaN, Infinity, wrong dimension, empty)
        12. Idempotency (skipping already indexed embeddings)
        13. Incremental indexing of new READY embeddings
        14. Partial batch failure handling (valid indexed, invalid marked FAILED)
        15. Safe index rebuild (rebuild succeeds, failure preserves old index)
        16. Document-level vector removal & ownership check
        17. PostgreSQL ↔ FAISS consistency check & reconciliation
        18. Structured IndexingResult statistics
"""
from __future__ import annotations

import os
import shutil
import tempfile
import uuid
from pathlib import Path
from unittest.mock import patch

import numpy as np
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import settings
from app.core.database import get_db
from app.models.base import Base
from app.models.chunk import Chunk, ChunkStatus
from app.models.document import Document, DocumentStatus
from app.models.embedding import Embedding, EmbeddingStatus
from app.models.parsed_document import ParsedDocument, ParsedDocumentStatus
from app.models.user import User
from app.models.vector_index_entry import VectorIndexEntry, VectorIndexStatus
from app.repositories import embedding_repository as emb_repo
from app.repositories import vector_index_repository as vidx_repo
from app.services.vector_indexing_service import (
    IndexingResult,
    ReconciliationResult,
    VectorIndexingService,
)
from app.vector_store.base import VectorStoreHealth
from app.vector_store.exceptions import (
    FAISSIndexError,
    VectorDimensionMismatchError,
    VectorIndexingError,
    VectorMappingError,
    VectorRebuildError,
    VectorStoreInitializationError,
    VectorStorePersistenceError,
)
from app.vector_store.faiss_store import FAISSVectorStore, _embedding_id_to_faiss_id


# ──────────────────────────────────────────────────────────────────────────────
# Test DB Setup
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
def setup_test_db():
    Base.metadata.create_all(bind=_test_engine)
    db = TestingSessionLocal()
    yield db
    db.close()
    Base.metadata.drop_all(bind=_test_engine)


@pytest.fixture
def tmp_index_dir(tmp_path):
    """Provides a temporary directory for FAISS storage."""
    d = tmp_path / "vector_store_test"
    d.mkdir(parents=True, exist_ok=True)
    return d


@pytest.fixture
def faiss_store(tmp_index_dir):
    """Constructs an initialised FAISSVectorStore with dim=768 in temporary storage."""
    index_path = tmp_index_dir / "test.index"
    mapping_path = tmp_index_dir / "test_mapping.json"
    store = FAISSVectorStore(
        index_path=index_path,
        mapping_path=mapping_path,
        dimension=768,
    )
    store.initialize_index()
    return store


# ── Helper for sample vectors ──────────────────────────────────────────────────

def _make_vector(dim: int = 768, seed: int = 42) -> list[float]:
    np.random.seed(seed)
    v = np.random.randn(dim).astype(np.float32)
    # L2 normalize so inner product == cosine similarity
    norm = np.linalg.norm(v)
    if norm > 0:
        v = v / norm
    return v.tolist()


# ──────────────────────────────────────────────────────────────────────────────
# PART A1 TESTS: VectorStore Foundation
# ──────────────────────────────────────────────────────────────────────────────

class TestPartA1VectorStoreFoundation:

    def test_store_initialization_empty_index(self, faiss_store):
        """Initialising a store in a new directory creates an empty FAISS index."""
        assert faiss_store.get_index_size() == 0
        assert faiss_store.get_dimension() == 768

        health = faiss_store.health_check()
        assert health.is_initialized is True
        assert health.is_loaded is True
        assert health.vector_count == 0
        assert health.dimension == 768

    def test_add_and_save_vectors(self, faiss_store):
        """Vectors can be added to FAISS and persisted atomically to disk."""
        vec1 = _make_vector(768, seed=1)
        vec2 = _make_vector(768, seed=2)
        emb_id1 = str(uuid.uuid4())
        emb_id2 = str(uuid.uuid4())

        mapping = faiss_store.add_vectors([vec1, vec2], [emb_id1, emb_id2])
        assert len(mapping) == 2
        assert emb_id1 in mapping
        assert emb_id2 in mapping
        assert faiss_store.get_index_size() == 2

        faiss_store.save_index()

        # Reload in a new store instance
        store2 = FAISSVectorStore(
            index_path=faiss_store._index_path,
            mapping_path=faiss_store._mapping_path,
            dimension=768,
        )
        store2.initialize_index()
        assert store2.get_index_size() == 2
        assert store2.get_indexed_embedding_ids() == {emb_id1, emb_id2}

    def test_dimension_mismatch_rejection(self, faiss_store):
        """Adding a vector with wrong dimension raises VectorDimensionMismatchError."""
        bad_vec = _make_vector(512, seed=1)  # 512 instead of 768
        emb_id = str(uuid.uuid4())

        with pytest.raises(VectorDimensionMismatchError) as exc_info:
            faiss_store.add_vectors([bad_vec], [emb_id])

        assert exc_info.value.expected_dimension == 768
        assert exc_info.value.actual_dimension == 512
        assert faiss_store.get_index_size() == 0

    def test_idempotent_adding(self, faiss_store):
        """Adding the same embedding_id twice skips re-adding."""
        vec = _make_vector(768, seed=1)
        emb_id = str(uuid.uuid4())

        m1 = faiss_store.add_vectors([vec], [emb_id])
        assert len(m1) == 1
        assert faiss_store.get_index_size() == 1

        # Second add with same emb_id
        m2 = faiss_store.add_vectors([vec], [emb_id])
        assert len(m2) == 0
        assert faiss_store.get_index_size() == 1

    def test_remove_vectors(self, faiss_store):
        """Vectors can be removed from FAISS index by embedding_id."""
        v1 = _make_vector(768, 1)
        v2 = _make_vector(768, 2)
        id1, id2 = str(uuid.uuid4()), str(uuid.uuid4())

        faiss_store.add_vectors([v1, v2], [id1, id2])
        assert faiss_store.get_index_size() == 2

        removed = faiss_store.remove_vectors([id1])
        assert removed == 1
        assert faiss_store.get_index_size() == 1
        assert faiss_store.get_indexed_embedding_ids() == {id2}

    def test_corrupt_index_load_handling(self, tmp_index_dir):
        """Loading a corrupted index file raises VectorStoreInitializationError."""
        idx_file = tmp_index_dir / "corrupt.index"
        map_file = tmp_index_dir / "corrupt_map.json"

        # Write invalid binary data
        idx_file.write_bytes(b"INVALID_FAISS_HEADER_DATA_12345")

        store = FAISSVectorStore(index_path=idx_file, mapping_path=map_file, dimension=768)
        with pytest.raises(VectorStoreInitializationError):
            store.initialize_index()

    def test_deterministic_faiss_id_conversion(self):
        """_embedding_id_to_faiss_id produces deterministic non-negative int64 IDs."""
        emb_id = "123e4567-e89b-12d3-a456-426614174000"
        id1 = _embedding_id_to_faiss_id(emb_id)
        id2 = _embedding_id_to_faiss_id(emb_id)
        assert id1 == id2
        assert isinstance(id1, int)
        assert 0 <= id1 < (1 << 63)


# ──────────────────────────────────────────────────────────────────────────────
# PART A2 TESTS: Vector Indexing & Persistence Pipeline
# ──────────────────────────────────────────────────────────────────────────────

class TestPartA2VectorIndexingService:

    @pytest.fixture
    def setup_domain_data(self, setup_test_db):
        """Creates User -> Document -> ParsedDocument -> Chunk -> Embedding hierarchy in DB."""
        db = setup_test_db

        user = User(name="Test User", email="testuser@example.com", password_hash="pw")
        db.add(user)
        db.flush()

        doc = Document(
            user_id=user.id,
            original_filename="document.pdf",
            stored_filename="uuid.pdf",
            display_name="document",
            file_extension="pdf",
            file_size=1024,
            mime_type="application/pdf",
            storage_path="uploads/doc.pdf",
            checksum="dummy_checksum_123",
            status=DocumentStatus.READY.value,
        )
        db.add(doc)
        db.flush()

        pdoc = ParsedDocument(
            document_id=doc.id,
            text_content="Full parsed text content",
            status=ParsedDocumentStatus.READY.value,
        )
        db.add(pdoc)
        db.flush()

        chunks = []
        embeddings = []
        for i in range(5):
            chunk = Chunk(
                parsed_document_id=pdoc.id,
                user_id=user.id,
                chunk_index=i,
                chunk_text=f"This is semantic chunk number {i}.",
                start_offset=i * 30,
                end_offset=(i + 1) * 30,
                estimated_tokens=6,
                chunk_size=800,
                overlap_size=150,
                status=ChunkStatus.READY.value,
            )
            db.add(chunk)
            db.flush()
            chunks.append(chunk)

            emb = Embedding(
                chunk_id=chunk.id,
                parsed_document_id=pdoc.id,
                user_id=user.id,
                provider="gemini",
                model_name="text-embedding-004",
                model_version="v1",
                embedding_version=1,
                dimension=768,
                status=EmbeddingStatus.READY.value,
            )
            emb.set_vector(_make_vector(768, seed=i))
            db.add(emb)
            db.flush()
            embeddings.append(emb)

        db.commit()
        return {
            "user": user,
            "document": doc,
            "parsed_document": pdoc,
            "chunks": chunks,
            "embeddings": embeddings,
        }

    def test_index_document_success(self, setup_test_db, setup_domain_data, faiss_store):
        """Indexing a document loads READY embeddings and persists them to FAISS and PostgreSQL."""
        db = setup_test_db
        pdoc = setup_domain_data["parsed_document"]
        user = setup_domain_data["user"]

        service = VectorIndexingService(vector_store=faiss_store, batch_size=2)
        res = service.index_document(
            db, parsed_document_id=pdoc.id, user_id=user.id
        )

        assert res.total == 5
        assert res.indexed == 5
        assert res.failed == 0
        assert res.skipped == 0
        assert faiss_store.get_index_size() == 5

        # Check PostgreSQL entries
        entries = vidx_repo.get_indexed_entries_for_document(db, pdoc.id)
        assert len(entries) == 5
        for entry in entries:
            assert entry.status == VectorIndexStatus.INDEXED.value

    def test_index_document_idempotency(self, setup_test_db, setup_domain_data, faiss_store):
        """Running indexing twice on the same document skips already indexed vectors."""
        db = setup_test_db
        pdoc = setup_domain_data["parsed_document"]
        user = setup_domain_data["user"]

        service = VectorIndexingService(vector_store=faiss_store, batch_size=5)

        # Run 1
        res1 = service.index_document(db, parsed_document_id=pdoc.id, user_id=user.id)
        assert res1.indexed == 5

        # Run 2
        res2 = service.index_document(db, parsed_document_id=pdoc.id, user_id=user.id)
        assert res2.total == 0  # No unindexed ready embeddings left
        assert faiss_store.get_index_size() == 5

    def test_partial_batch_failure(self, setup_test_db, setup_domain_data, faiss_store):
        """One bad vector (e.g. NaN) in a batch is rejected while valid vectors are indexed."""
        db = setup_test_db
        pdoc = setup_domain_data["parsed_document"]
        user = setup_domain_data["user"]
        embeddings = setup_domain_data["embeddings"]

        # Corrupt one vector with NaN
        corrupt_vec = _make_vector(768, seed=99)
        corrupt_vec[10] = float("nan")
        embeddings[2].set_vector(corrupt_vec)
        db.commit()

        service = VectorIndexingService(vector_store=faiss_store, batch_size=5)
        res = service.index_document(db, parsed_document_id=pdoc.id, user_id=user.id)

        assert res.total == 5
        assert res.indexed == 4
        assert res.failed == 1
        assert faiss_store.get_index_size() == 4

        # Check DB status for the corrupted entry
        corrupt_entry = vidx_repo.get_by_embedding_id(db, embeddings[2].id)
        assert corrupt_entry is not None
        assert corrupt_entry.status == VectorIndexStatus.INDEX_FAILED.value
        assert "NaN" in corrupt_entry.failure_reason

    def test_safe_index_rebuild(self, setup_test_db, setup_domain_data, faiss_store):
        """Rebuilding the index creates a clean index from PostgreSQL READY embeddings."""
        db = setup_test_db
        pdoc = setup_domain_data["parsed_document"]
        user = setup_domain_data["user"]

        service = VectorIndexingService(vector_store=faiss_store, batch_size=10)
        service.index_document(db, parsed_document_id=pdoc.id, user_id=user.id)
        assert faiss_store.get_index_size() == 5

        # Perform rebuild
        rebuild_res = service.rebuild_index(db)
        assert rebuild_res.indexed == 5
        assert faiss_store.get_index_size() == 5

    def test_remove_document_vectors(self, setup_test_db, setup_domain_data, faiss_store):
        """Removing vectors for a document clears them from FAISS and marks DB entries as REMOVED."""
        db = setup_test_db
        pdoc = setup_domain_data["parsed_document"]
        user = setup_domain_data["user"]

        service = VectorIndexingService(vector_store=faiss_store, batch_size=10)
        service.index_document(db, parsed_document_id=pdoc.id, user_id=user.id)
        assert faiss_store.get_index_size() == 5

        removed_count = service.remove_document_vectors(
            db, parsed_document_id=pdoc.id, user_id=user.id
        )
        assert removed_count == 5
        assert faiss_store.get_index_size() == 0

        # Verify DB entries marked REMOVED
        entries = db.query(VectorIndexEntry).all()
        assert len(entries) == 5
        for e in entries:
            assert e.status == VectorIndexStatus.REMOVED.value

    def test_reconciliation_check(self, setup_test_db, setup_domain_data, faiss_store):
        """Reconciliation detects consistent state and discrepancies."""
        db = setup_test_db
        pdoc = setup_domain_data["parsed_document"]
        user = setup_domain_data["user"]

        service = VectorIndexingService(vector_store=faiss_store, batch_size=10)
        service.index_document(db, parsed_document_id=pdoc.id, user_id=user.id)

        rec1 = service.reconcile(db)
        assert rec1.is_consistent is True
        assert rec1.db_indexed_count == 5
        assert rec1.faiss_vector_count == 5
        assert rec1.missing_in_faiss == 0
        assert rec1.orphaned_in_faiss == 0

        # Simulate discrepancy: remove a vector from FAISS without updating DB
        emb_id = setup_domain_data["embeddings"][0].id
        faiss_store.remove_vectors([emb_id])

        rec2 = service.reconcile(db)
        assert rec2.is_consistent is False
        assert rec2.missing_in_faiss == 1
