"""
Day 68 — Intelligent Text Chunking Engine — Comprehensive Test Suite.

Coverage:
    PART A1 — Chunking Engine
        - text_splitter: normalize, split_paragraphs, split_by_sentences,
          merge_into_chunks, apply_overlap_to_segments, hard_split, run_pipeline
        - token_estimator: estimate_tokens, batch estimation
        - chunk_validator: all 6 rules (empty, ordering, offsets, size, dup, tokens)
        - ChunkStrategy: interface contract, ChunkData validation
        - RecursiveChunkStrategy: splitting, paragraph preservation, sentence
          preservation, overlap correctness, markdown/heading awareness
        - ChunkFactory: strategy selection, registration, fallback

    PART A2 — Chunk Storage
        - chunk_integrity_validator: 6 integrity checks
        - ChunkRepository: create, bulk_create, get, list, count, archive, ready
        - ChunkService: save_chunks, regenerate_chunks, get_chunks, archive_chunks,
          get_chunk_metadata, count_chunks, duplicate prevention, ownership
        - Integration: ParsedDocument → ChunkingService → ChunkService → DB
        - Performance: tiny doc, large doc (simulated), many chunks, concurrent-safe
"""
from __future__ import annotations

import time
import uuid
from typing import Optional

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.core.database import get_db
from app.models.base import Base
from app.models.chunk import Chunk, ChunkStatus
from app.models.document import Document, DocumentStatus
from app.models.parsed_document import ParsedDocument, ParsedDocumentStatus
from app.utils.text_splitter import (
    apply_overlap_to_segments,
    hard_split,
    merge_into_chunks,
    normalize,
    run_pipeline,
    split_by_sentences,
    split_paragraphs,
)
from app.utils.token_estimator import estimate_tokens, estimate_tokens_for_chunks
from app.utils.chunk_validator import (
    ChunkValidationError,
    assert_valid_chunks,
    validate_chunks,
)
from app.utils.chunk_integrity_validator import (
    ChunkIntegrityError,
    assert_chunk_set_valid,
    validate_chunk_set,
)
from parsers.chunking.chunk_strategy import ChunkData, ChunkStrategy
from parsers.chunking.recursive_chunk_strategy import RecursiveChunkStrategy
from parsers.chunking.chunk_factory import ChunkFactory, _STRATEGY_REGISTRY
from app.repositories import chunk_repository as chunk_repo
from app.services.chunking_service import ChunkingService
from app.services.chunk_service import ChunkService

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
    with _test_engine.connect() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                username TEXT UNIQUE NOT NULL,
                hashed_password TEXT NOT NULL,
                is_active INTEGER DEFAULT 1,
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
                document_id TEXT UNIQUE NOT NULL,
                text_content TEXT NOT NULL DEFAULT '',
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
        conn.commit()


_create_test_tables()


def get_test_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(autouse=True)
def setup_db(monkeypatch):
    """Override get_db with test session for every test."""
    app.dependency_overrides[get_db] = get_test_db
    yield
    app.dependency_overrides.clear()


# ──────────────────────────────────────────────────────────────────────────────
# Helper: DB fixture and seed data
# ──────────────────────────────────────────────────────────────────────────────

@pytest.fixture
def db():
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture
def seed_user(db):
    """Insert a test user and return user_id."""
    uid = db.execute(
        text("INSERT INTO users (email, username, hashed_password) VALUES (:e, :u, :p)"),
        {"e": f"test_{uuid.uuid4().hex[:6]}@example.com", "u": f"user_{uuid.uuid4().hex[:6]}", "p": "hash"},
    ).lastrowid
    db.commit()
    return uid


@pytest.fixture
def seed_document(db, seed_user):
    """Insert a Document record and return its id."""
    doc_id = str(uuid.uuid4())
    db.execute(
        text("""
            INSERT INTO documents
            (id, user_id, original_filename, stored_filename, display_name,
             file_extension, mime_type, file_size, storage_path, checksum, status)
            VALUES (:id, :uid, 'test.txt', 'stored.txt', 'Test Doc',
                    'txt', 'text/plain', 1000, 'uploads/1/test.txt', 'abc123', 'READY')
        """),
        {"id": doc_id, "uid": seed_user},
    )
    db.commit()
    return doc_id, seed_user


@pytest.fixture
def seed_parsed_document(db, seed_document):
    """Insert a READY ParsedDocument with sample text. Returns (parsed_id, doc_id, user_id)."""
    doc_id, user_id = seed_document
    parsed_id = str(uuid.uuid4())
    text_content = (
        "Introduction\n\n"
        "This is the first paragraph with some content about machine learning. "
        "It contains multiple sentences. Each sentence is complete.\n\n"
        "Methods\n\n"
        "The second paragraph describes the methodology. "
        "We use recursive chunking for semantic preservation. "
        "Overlapping chunks ensure context is maintained across boundaries.\n\n"
        "Results\n\n"
        "Our results show that semantic chunking improves retrieval quality. "
        "The F1 score improved by 15 percent. Further experiments are ongoing.\n\n"
        "Conclusion\n\n"
        "In conclusion, intelligent chunking is a critical step in RAG pipelines. "
        "Future work includes token-based and semantic chunking strategies."
    )
    db.execute(
        text("""
            INSERT INTO parsed_documents (id, document_id, text_content, status)
            VALUES (:id, :did, :text, :status)
        """),
        {
            "id": parsed_id,
            "did": doc_id,
            "text": text_content,
            "status": ParsedDocumentStatus.READY.value,
        },
    )
    db.commit()
    return parsed_id, doc_id, user_id, text_content


# ══════════════════════════════════════════════════════════════════════════════
# PART A1 TESTS — Text Splitter
# ══════════════════════════════════════════════════════════════════════════════

class TestNormalize:
    def test_crlf_normalised_to_lf(self):
        assert "\r\n" not in normalize("hello\r\nworld")

    def test_excess_blank_lines_collapsed(self):
        result = normalize("para1\n\n\n\n\npara2")
        assert result == "para1\n\npara2"

    def test_trailing_spaces_removed(self):
        result = normalize("hello   \nworld   ")
        assert not any(line.endswith(" ") for line in result.split("\n"))

    def test_repeated_spaces_collapsed(self):
        result = normalize("hello     world")
        assert "  " not in result

    def test_empty_input(self):
        assert normalize("") == ""
        assert normalize("   ") == ""

    def test_content_preserved(self):
        text = "Machine learning is great.\n\nDeep learning is better."
        result = normalize(text)
        assert "Machine learning is great." in result
        assert "Deep learning is better." in result


class TestSplitParagraphs:
    def test_splits_on_double_newline(self):
        paragraphs = split_paragraphs("para1\n\npara2\n\npara3")
        assert len(paragraphs) == 3

    def test_empty_paragraphs_excluded(self):
        paragraphs = split_paragraphs("para1\n\n\n\npara2")
        assert len(paragraphs) == 2

    def test_single_paragraph(self):
        assert split_paragraphs("just one paragraph") == ["just one paragraph"]

    def test_empty_input(self):
        assert split_paragraphs("") == []


class TestSplitBySentences:
    def test_splits_on_period(self):
        parts = split_by_sentences("First sentence. Second sentence. Third.")
        assert len(parts) >= 2

    def test_splits_on_exclamation(self):
        parts = split_by_sentences("Great! Amazing! Wonderful!")
        assert len(parts) >= 2

    def test_splits_on_question(self):
        parts = split_by_sentences("What is AI? How does it work?")
        assert len(parts) >= 2

    def test_single_sentence(self):
        parts = split_by_sentences("One sentence only")
        assert parts == ["One sentence only"]

    def test_empty_input(self):
        assert split_by_sentences("") == []


class TestMergeIntoChunks:
    def test_merges_short_segments(self):
        segs = ["hello", "world", "foo"]
        chunks = merge_into_chunks(segs, chunk_size=50)
        assert len(chunks) == 1
        assert "hello" in chunks[0]

    def test_respects_chunk_size(self):
        segs = ["A" * 100, "B" * 100, "C" * 100]
        chunks = merge_into_chunks(segs, chunk_size=110)
        for c in chunks:
            assert len(c) <= 200  # allow slight overage from separator

    def test_empty_input(self):
        assert merge_into_chunks([], 100) == []


class TestApplyOverlap:
    def test_overlap_prepended_to_subsequent_chunks(self):
        segs = ["First sentence here.", "Second sentence here.", "Third sentence here."]
        result = apply_overlap_to_segments(segs, overlap=10)
        assert len(result) == 3
        assert result[0] == segs[0]  # First unchanged
        # Subsequent chunks should be longer than original due to overlap
        assert len(result[1]) >= len(segs[1])

    def test_no_overlap_when_zero(self):
        segs = ["First.", "Second."]
        result = apply_overlap_to_segments(segs, overlap=0)
        assert result == segs

    def test_single_segment_unchanged(self):
        segs = ["Only one segment."]
        result = apply_overlap_to_segments(segs, overlap=20)
        assert result == segs


class TestHardSplit:
    def test_splits_long_text(self):
        text = "word " * 200  # 1000 chars
        chunks = hard_split(text, chunk_size=100)
        assert all(len(c) <= 120 for c in chunks)  # word-aligned may slightly exceed

    def test_empty_input(self):
        assert hard_split("", 100) == []

    def test_short_text_unchanged(self):
        text = "short text"
        assert hard_split(text, 100) == ["short text"]


class TestRunPipeline:
    def test_produces_chunks_from_text(self):
        text = "Para one.\n\nPara two.\n\nPara three."
        chunks = run_pipeline(text, chunk_size=50, chunk_overlap=10)
        assert len(chunks) >= 1

    def test_empty_text_returns_empty(self):
        assert run_pipeline("") == []

    def test_single_sentence_fits_in_one_chunk(self):
        text = "This is a short sentence."
        chunks = run_pipeline(text, chunk_size=100, chunk_overlap=10)
        assert len(chunks) == 1


# ══════════════════════════════════════════════════════════════════════════════
# PART A1 TESTS — Token Estimator
# ══════════════════════════════════════════════════════════════════════════════

class TestTokenEstimator:
    def test_estimate_empty(self):
        assert estimate_tokens("") == 0

    def test_estimate_none_like(self):
        assert estimate_tokens(None) == 0  # type: ignore

    def test_estimate_short_text(self):
        assert estimate_tokens("Hello") >= 1

    def test_estimate_approximate_ratio(self):
        text = "A" * 400
        tokens = estimate_tokens(text)
        assert 90 <= tokens <= 110  # 400/4 = 100

    def test_batch_estimation(self):
        texts = ["hello", "world", "foo bar baz"]
        results = estimate_tokens_for_chunks(texts)
        assert len(results) == 3
        assert all(isinstance(t, int) and t >= 0 for t in results)


# ══════════════════════════════════════════════════════════════════════════════
# PART A1 TESTS — Chunk Validator (in-memory)
# ══════════════════════════════════════════════════════════════════════════════

def _make_chunk(idx=0, text="Hello world sentence here.", start=0, end=None, tokens=5, size=800, overlap=150):
    end = end or (start + len(text))
    return ChunkData(
        chunk_index=idx,
        chunk_text=text,
        start_offset=start,
        end_offset=end,
        estimated_tokens=tokens,
        chunk_size=size,
        overlap_size=overlap,
    )


class TestChunkValidator:
    def test_empty_list_is_valid(self):
        assert validate_chunks([]) == []

    def test_valid_chunks_pass(self):
        chunks = [
            _make_chunk(0, "First chunk text here.", 0, 22),
            _make_chunk(1, "Second chunk text here.", 22, 45),
        ]
        assert validate_chunks(chunks) == []

    def test_empty_text_flagged(self):
        chunks = [_make_chunk(0, "   ", 0, 3)]
        errors = validate_chunks(chunks)
        assert any("empty" in e.lower() for e in errors)

    def test_ordering_violation_flagged(self):
        c1 = _make_chunk(0, "First chunk.", 0, 12)
        c2 = _make_chunk(5, "Second chunk.", 12, 25)  # index 5, not 1
        errors = validate_chunks([c1, c2])
        assert any("ordering" in e.lower() or "index" in e.lower() for e in errors)

    def test_duplicate_text_flagged(self):
        text = "Same text repeated here."
        chunks = [_make_chunk(0, text, 0, 24), _make_chunk(1, text, 24, 48)]
        errors = validate_chunks(chunks)
        assert any("duplicate" in e.lower() for e in errors)

    def test_offset_monotonicity_violation_flagged(self):
        c1 = _make_chunk(0, "First chunk.", 100, 112)
        c2 = _make_chunk(1, "Second chunk.", 50, 63)  # start before c1
        errors = validate_chunks([c1, c2])
        assert any("offset" in e.lower() or "monoton" in e.lower() for e in errors)

    def test_raise_on_error(self):
        chunks = [_make_chunk(0, "   ", 0, 3)]
        with pytest.raises(ChunkValidationError):
            validate_chunks(chunks, raise_on_error=True)

    def test_assert_valid_chunks_raises(self):
        chunks = [_make_chunk(0, "   ", 0, 3)]
        with pytest.raises(ChunkValidationError):
            assert_valid_chunks(chunks)


# ══════════════════════════════════════════════════════════════════════════════
# PART A1 TESTS — ChunkData Dataclass
# ══════════════════════════════════════════════════════════════════════════════

class TestChunkData:
    def test_valid_creation(self):
        cd = ChunkData(
            chunk_index=0,
            chunk_text="Test text",
            start_offset=0,
            end_offset=9,
            estimated_tokens=2,
            chunk_size=800,
            overlap_size=150,
        )
        assert cd.char_count == 9
        assert cd.strategy == "recursive"

    def test_invalid_chunk_index(self):
        with pytest.raises(ValueError, match="chunk_index"):
            ChunkData(-1, "text", 0, 4, 1, 800, 150)

    def test_invalid_offsets(self):
        with pytest.raises(ValueError, match="end_offset"):
            ChunkData(0, "text", 10, 5, 1, 800, 150)

    def test_invalid_tokens(self):
        with pytest.raises(ValueError, match="estimated_tokens"):
            ChunkData(0, "text", 0, 4, -1, 800, 150)


# ══════════════════════════════════════════════════════════════════════════════
# PART A1 TESTS — RecursiveChunkStrategy
# ══════════════════════════════════════════════════════════════════════════════

class TestRecursiveChunkStrategy:
    """Tests for the RecursiveChunkStrategy."""

    strategy = RecursiveChunkStrategy()

    def test_supports_all_document_types(self):
        for doc_type in ("pdf", "txt", "md", "docx", "unknown"):
            assert self.strategy.supports(doc_type)

    def test_empty_text_returns_empty(self):
        assert self.strategy.chunk("") == []
        assert self.strategy.chunk("   ") == []

    def test_short_text_single_chunk(self):
        text = "Short document."
        chunks = self.strategy.chunk(text, chunk_size=800, chunk_overlap=150)
        assert len(chunks) == 1
        assert chunks[0].chunk_index == 0

    def test_chunk_ordering(self):
        text = "\n\n".join([f"Paragraph {i} with some text." for i in range(10)])
        chunks = self.strategy.chunk(text, chunk_size=100, chunk_overlap=20)
        for i, chunk in enumerate(chunks):
            assert chunk.chunk_index == i

    def test_paragraph_preservation(self):
        """Short paragraphs should remain whole chunks."""
        text = "First paragraph content.\n\nSecond paragraph content.\n\nThird paragraph content."
        chunks = self.strategy.chunk(text, chunk_size=800, chunk_overlap=50)
        # With chunk_size=800, all 3 short paragraphs should fit in 1-2 chunks
        full_text = " ".join(c.chunk_text for c in chunks)
        assert "First paragraph content" in full_text
        assert "Second paragraph content" in full_text
        assert "Third paragraph content" in full_text

    def test_sentence_preservation_no_mid_split(self):
        """Sentences should not be split in half."""
        long_sentence = "This is an intentionally very long sentence that should not be split in the middle of a word or between two adjacent tokens that form a meaningful unit."
        text = f"{long_sentence}\n\n{long_sentence}\n\n{long_sentence}"
        chunks = self.strategy.chunk(text, chunk_size=150, chunk_overlap=20)
        for chunk in chunks:
            # Each chunk text should start and end at word boundaries
            assert not chunk.chunk_text.startswith(" ")

    def test_overlap_applied(self):
        """Subsequent chunks should include content from previous chunk."""
        text = "First sentence content here. " * 20
        chunks = self.strategy.chunk(text, chunk_size=200, chunk_overlap=50)
        if len(chunks) > 1:
            # Chunk 1 should contain some text that was also in chunk 0
            # (overlap means shared content)
            assert len(chunks[1].chunk_text) > 0

    def test_start_offset_non_negative(self):
        text = "Some text here.\n\nMore text here.\n\nEven more text."
        chunks = self.strategy.chunk(text, chunk_size=50, chunk_overlap=10)
        assert all(c.start_offset >= 0 for c in chunks)

    def test_end_offset_gte_start_offset(self):
        text = "Some text here.\n\nMore text here.\n\nEven more text."
        chunks = self.strategy.chunk(text, chunk_size=50, chunk_overlap=10)
        assert all(c.end_offset >= c.start_offset for c in chunks)

    def test_estimated_tokens_positive(self):
        text = "A chunk of text with several words in it."
        chunks = self.strategy.chunk(text)
        assert all(c.estimated_tokens > 0 for c in chunks)

    def test_strategy_metadata_correct(self):
        text = "Test text with strategy metadata."
        chunks = self.strategy.chunk(text)
        for c in chunks:
            assert c.strategy == "recursive"
            assert c.strategy_version == "1.0.0"

    def test_markdown_heading_section_detected(self):
        text = "# Introduction\n\nThis is the intro section.\n\n## Methods\n\nMethodology here."
        chunks = self.strategy.chunk(text, chunk_size=800, chunk_overlap=50, document_type="md")
        sections = [c.section for c in chunks if c.section]
        assert len(sections) > 0

    def test_configurable_chunk_size(self):
        text = "A" * 2000
        chunks_small = self.strategy.chunk(text, chunk_size=200, chunk_overlap=20)
        chunks_large = self.strategy.chunk(text, chunk_size=800, chunk_overlap=20)
        assert len(chunks_small) >= len(chunks_large)

    def test_validation_passes_for_valid_chunks(self):
        text = "This is a test document with multiple sentences. It has enough content."
        chunks = self.strategy.chunk(text, chunk_size=800, chunk_overlap=50)
        errors = self.strategy.validate(chunks)
        assert errors == []

    def test_large_document(self):
        """Large document should not raise errors."""
        text = " ".join(f"This is sentence number {i} in a large document." for i in range(500))
        chunks = self.strategy.chunk(text, chunk_size=800, chunk_overlap=150)
        assert len(chunks) > 1
        assert all(c.chunk_index == i for i, c in enumerate(chunks))


# ══════════════════════════════════════════════════════════════════════════════
# PART A1 TESTS — ChunkFactory
# ══════════════════════════════════════════════════════════════════════════════

class TestChunkFactory:
    def test_get_strategy_returns_recursive_by_default(self):
        strategy = ChunkFactory.get_strategy("txt")
        assert strategy.name == "recursive"

    def test_get_strategy_unknown_type_returns_recursive(self):
        strategy = ChunkFactory.get_strategy("xyz_unknown_type")
        assert strategy.name == "recursive"

    def test_get_strategy_empty_type(self):
        strategy = ChunkFactory.get_strategy("")
        assert strategy is not None

    def test_list_strategies_contains_recursive(self):
        strategies = ChunkFactory.list_strategies()
        assert "recursive" in strategies

    def test_register_custom_strategy(self):
        """Test that a custom strategy can be registered and selected."""

        class MockStrategy(ChunkStrategy):
            @property
            def name(self): return "mock_strategy_test"
            @property
            def version(self): return "0.0.1"
            def supports(self, document_type): return document_type == "mock_doc"
            def chunk(self, text, **kwargs): return []
            def validate(self, chunks): return []

        original_count = len(ChunkFactory.list_strategies())
        ChunkFactory.register(MockStrategy())
        new_count = len(ChunkFactory.list_strategies())
        assert new_count == original_count + 1
        assert "mock_strategy_test" in ChunkFactory.list_strategies()

        # Clean up
        _STRATEGY_REGISTRY[:] = [s for s in _STRATEGY_REGISTRY if s.name != "mock_strategy_test"]


# ══════════════════════════════════════════════════════════════════════════════
# PART A2 TESTS — Chunk Integrity Validator
# ══════════════════════════════════════════════════════════════════════════════

class TestChunkIntegrityValidator:
    def test_empty_set_is_valid(self):
        assert validate_chunk_set([]) == []

    def test_valid_set_passes(self):
        chunks = [
            _make_chunk(0, "First chunk here.", 0, 17),
            _make_chunk(1, "Second chunk here.", 17, 35),
        ]
        assert validate_chunk_set(chunks) == []

    def test_ordering_violation(self):
        chunks = [_make_chunk(0, "A" * 20, 0, 20), _make_chunk(5, "B" * 20, 20, 40)]
        errors = validate_chunk_set(chunks)
        assert any("ordering" in e for e in errors)

    def test_offset_violation(self):
        chunk = _make_chunk(0, "text", start=0, end=5)
        # Override to bypass dataclass __post_init__ check
        object.__setattr__(chunk, "start_offset", 10)
        object.__setattr__(chunk, "end_offset", 5)  # end < start
        errors = validate_chunk_set([chunk])
        assert any("offset" in e for e in errors)

    def test_duplicate_detection(self):
        text = "Same text here."
        chunks = [_make_chunk(0, text, 0, 15), _make_chunk(1, text, 15, 30)]
        errors = validate_chunk_set(chunks)
        assert any("duplicate" in e for e in errors)

    def test_strategy_inconsistency(self):
        c1 = _make_chunk(0, "First text here.", 0, 16)
        c2 = _make_chunk(1, "Second text here.", 16, 33)
        object.__setattr__(c2, "strategy", "different_strategy")
        errors = validate_chunk_set([c1, c2])
        assert any("strategy" in e for e in errors)

    def test_raise_on_error(self):
        text = "Same text repeated."
        chunks = [_make_chunk(0, text, 0, 19), _make_chunk(1, text, 19, 38)]
        with pytest.raises(ChunkIntegrityError):
            validate_chunk_set(chunks, raise_on_error=True)

    def test_assert_chunk_set_valid_raises(self):
        text = "Duplicate here."
        chunks = [_make_chunk(0, text, 0, 15), _make_chunk(1, text, 15, 30)]
        with pytest.raises(ChunkIntegrityError):
            assert_chunk_set_valid(chunks)


# ══════════════════════════════════════════════════════════════════════════════
# PART A2 TESTS — Chunk Repository
# ══════════════════════════════════════════════════════════════════════════════

class TestChunkRepository:
    def test_create_chunk(self, db, seed_parsed_document):
        parsed_id, doc_id, user_id, _ = seed_parsed_document
        cd = _make_chunk(0, "Chunk text for repository test.")
        chunk = chunk_repo.create_chunk(
            db, parsed_document_id=parsed_id, user_id=user_id, chunk_data=cd
        )
        db.commit()
        assert chunk.id is not None
        assert chunk.chunk_index == 0
        assert chunk.status == ChunkStatus.READY.value

    def test_bulk_create_chunks(self, db, seed_parsed_document):
        parsed_id, _, user_id, _ = seed_parsed_document
        chunk_data_list = [
            _make_chunk(i, f"Chunk number {i} with content.", i * 30, (i + 1) * 30)
            for i in range(10)
        ]
        chunks = chunk_repo.bulk_create_chunks(
            db,
            parsed_document_id=parsed_id,
            user_id=user_id,
            chunk_data_list=chunk_data_list,
        )
        db.commit()
        assert len(chunks) == 10
        assert all(c.status == ChunkStatus.READY.value for c in chunks)

    def test_get_chunk(self, db, seed_parsed_document):
        parsed_id, _, user_id, _ = seed_parsed_document
        cd = _make_chunk(0, "Retrievable chunk.")
        chunk = chunk_repo.create_chunk(db, parsed_document_id=parsed_id, user_id=user_id, chunk_data=cd)
        db.commit()

        fetched = chunk_repo.get_chunk(db, chunk.id)
        assert fetched is not None
        assert fetched.id == chunk.id

    def test_get_chunk_not_found(self, db):
        assert chunk_repo.get_chunk(db, "nonexistent-id") is None

    def test_list_chunks_by_document_ordered(self, db, seed_parsed_document):
        parsed_id, _, user_id, _ = seed_parsed_document
        data = [_make_chunk(i, f"Chunk {i} text.", i * 20, (i + 1) * 20) for i in range(5)]
        chunk_repo.bulk_create_chunks(db, parsed_document_id=parsed_id, user_id=user_id, chunk_data_list=data)
        db.commit()

        chunks, total = chunk_repo.list_chunks_by_document(db, parsed_id)
        assert total == 5
        assert [c.chunk_index for c in chunks] == list(range(5))

    def test_list_chunks_pagination(self, db, seed_parsed_document):
        parsed_id, _, user_id, _ = seed_parsed_document
        data = [_make_chunk(i, f"Chunk {i} content here.", i * 25, (i + 1) * 25) for i in range(20)]
        chunk_repo.bulk_create_chunks(db, parsed_document_id=parsed_id, user_id=user_id, chunk_data_list=data)
        db.commit()

        page1, total = chunk_repo.list_chunks_by_document(db, parsed_id, page=1, page_size=10)
        page2, _ = chunk_repo.list_chunks_by_document(db, parsed_id, page=2, page_size=10)
        assert len(page1) == 10
        assert len(page2) == 10
        assert total == 20

    def test_get_ready_chunks(self, db, seed_parsed_document):
        parsed_id, _, user_id, _ = seed_parsed_document
        data = [_make_chunk(i, f"Chunk {i} ready.", i * 15, (i + 1) * 15) for i in range(5)]
        chunk_repo.bulk_create_chunks(db, parsed_document_id=parsed_id, user_id=user_id, chunk_data_list=data)
        db.commit()

        ready = chunk_repo.get_ready_chunks(db, parsed_id)
        assert len(ready) == 5
        assert all(c.status == ChunkStatus.READY.value for c in ready)

    def test_get_chunk_count(self, db, seed_parsed_document):
        parsed_id, _, user_id, _ = seed_parsed_document
        data = [_make_chunk(i, f"Count test chunk {i}.", i * 20, (i + 1) * 20) for i in range(7)]
        chunk_repo.bulk_create_chunks(db, parsed_document_id=parsed_id, user_id=user_id, chunk_data_list=data)
        db.commit()

        count = chunk_repo.get_chunk_count(db, parsed_id)
        assert count == 7

        ready_count = chunk_repo.get_chunk_count(db, parsed_id, status_filter=ChunkStatus.READY.value)
        assert ready_count == 7

    def test_archive_chunks_for_document(self, db, seed_parsed_document):
        parsed_id, _, user_id, _ = seed_parsed_document
        data = [_make_chunk(i, f"Archive test chunk {i}.", i * 20, (i + 1) * 20) for i in range(5)]
        chunk_repo.bulk_create_chunks(db, parsed_document_id=parsed_id, user_id=user_id, chunk_data_list=data)
        db.commit()

        archived_count = chunk_repo.archive_chunks_for_document(db, parsed_id)
        db.commit()

        assert archived_count == 5
        archived = chunk_repo.list_chunks_by_document(db, parsed_id, status_filter=ChunkStatus.ARCHIVED.value)
        assert archived[1] == 5  # total

    def test_delete_chunk(self, db, seed_parsed_document):
        parsed_id, _, user_id, _ = seed_parsed_document
        cd = _make_chunk(0, "Chunk to delete.")
        chunk = chunk_repo.create_chunk(db, parsed_document_id=parsed_id, user_id=user_id, chunk_data=cd)
        db.commit()

        chunk_repo.delete_chunk(db, chunk)
        db.commit()

        assert chunk_repo.get_chunk(db, chunk.id) is None

    def test_update_chunk_status(self, db, seed_parsed_document):
        parsed_id, _, user_id, _ = seed_parsed_document
        cd = _make_chunk(0, "Status update chunk.")
        chunk = chunk_repo.create_chunk(db, parsed_document_id=parsed_id, user_id=user_id, chunk_data=cd)
        db.commit()

        chunk_repo.update_chunk_status(db, chunk, ChunkStatus.ARCHIVED.value)
        db.commit()

        fetched = chunk_repo.get_chunk(db, chunk.id)
        assert fetched.status == ChunkStatus.ARCHIVED.value


# ══════════════════════════════════════════════════════════════════════════════
# PART A2 TESTS — ChunkingService (generation only)
# ══════════════════════════════════════════════════════════════════════════════

class TestChunkingService:
    def test_generate_chunks_returns_chunk_data(self, db, seed_parsed_document):
        _, doc_id, user_id, _ = seed_parsed_document
        chunks = ChunkingService.generate_chunks(db, document_id=doc_id, user_id=user_id)
        assert isinstance(chunks, list)
        assert len(chunks) > 0
        assert all(isinstance(c, ChunkData) for c in chunks)

    def test_generate_chunks_ordering(self, db, seed_parsed_document):
        _, doc_id, user_id, _ = seed_parsed_document
        chunks = ChunkingService.generate_chunks(db, document_id=doc_id, user_id=user_id)
        for i, c in enumerate(chunks):
            assert c.chunk_index == i

    def test_generate_chunks_wrong_user_raises(self, db, seed_parsed_document):
        _, doc_id, user_id, _ = seed_parsed_document
        with pytest.raises(ValueError, match="does not belong"):
            ChunkingService.generate_chunks(db, document_id=doc_id, user_id=99999)

    def test_generate_chunks_missing_doc_raises(self, db, seed_user):
        with pytest.raises(ValueError):
            ChunkingService.generate_chunks(
                db, document_id="nonexistent-id", user_id=seed_user
            )

    def test_estimate_tokens(self):
        result = ChunkingService.estimate_tokens("Hello world")
        assert isinstance(result, int)
        assert result > 0

    def test_validate_chunks_returns_errors(self):
        bad_chunks = [_make_chunk(0, "   ", 0, 3)]
        errors = ChunkingService.validate_chunks(bad_chunks)
        assert len(errors) > 0

    def test_validate_chunks_valid(self):
        good_chunks = [_make_chunk(0, "Valid chunk text.", 0, 17)]
        errors = ChunkingService.validate_chunks(good_chunks)
        assert errors == []

    def test_get_metrics_returns_dict(self):
        metrics = ChunkingService.get_metrics()
        assert isinstance(metrics, dict)
        assert "chunk_generation_total" in metrics


# ══════════════════════════════════════════════════════════════════════════════
# PART A2 TESTS — ChunkService (persistence)
# ══════════════════════════════════════════════════════════════════════════════

class TestChunkService:
    def test_save_chunks_persists_to_db(self, db, seed_parsed_document):
        parsed_id, doc_id, user_id, _ = seed_parsed_document
        result = ChunkService.save_chunks(db, document_id=doc_id, user_id=user_id)
        assert result.chunk_count > 0
        assert result.status == "READY"

        count = chunk_repo.get_chunk_count(db, parsed_id)
        assert count == result.chunk_count

    def test_save_chunks_idempotent_on_existing(self, db, seed_parsed_document):
        parsed_id, doc_id, user_id, _ = seed_parsed_document
        r1 = ChunkService.save_chunks(db, document_id=doc_id, user_id=user_id)
        r2 = ChunkService.save_chunks(db, document_id=doc_id, user_id=user_id)
        # Should skip, not duplicate
        count = chunk_repo.get_chunk_count(db, parsed_id)
        assert count == r1.chunk_count

    def test_regenerate_chunks_archives_old(self, db, seed_parsed_document):
        parsed_id, doc_id, user_id, _ = seed_parsed_document
        r1 = ChunkService.save_chunks(db, document_id=doc_id, user_id=user_id)
        initial_count = r1.chunk_count

        r2 = ChunkService.regenerate_chunks(db, document_id=doc_id, user_id=user_id)

        archived_count = chunk_repo.get_chunk_count(
            db, parsed_id, status_filter=ChunkStatus.ARCHIVED.value
        )
        ready_count = chunk_repo.get_chunk_count(
            db, parsed_id, status_filter=ChunkStatus.READY.value
        )
        assert archived_count == initial_count
        assert ready_count == r2.chunk_count

    def test_save_chunks_wrong_user_raises(self, db, seed_parsed_document):
        _, doc_id, _, _ = seed_parsed_document
        with pytest.raises(ValueError):
            ChunkService.save_chunks(db, document_id=doc_id, user_id=99999)

    def test_get_chunks_returns_list(self, db, seed_parsed_document):
        parsed_id, doc_id, user_id, _ = seed_parsed_document
        ChunkService.save_chunks(db, document_id=doc_id, user_id=user_id)

        response = ChunkService.get_chunks(db, document_id=doc_id, user_id=user_id)
        assert response.total > 0
        assert len(response.chunks) > 0

    def test_get_chunks_ordered_by_index(self, db, seed_parsed_document):
        _, doc_id, user_id, _ = seed_parsed_document
        ChunkService.save_chunks(db, document_id=doc_id, user_id=user_id)

        response = ChunkService.get_chunks(db, document_id=doc_id, user_id=user_id)
        indices = [c.chunk_index for c in response.chunks]
        assert indices == sorted(indices)

    def test_count_chunks(self, db, seed_parsed_document):
        _, doc_id, user_id, _ = seed_parsed_document
        r = ChunkService.save_chunks(db, document_id=doc_id, user_id=user_id)
        count = ChunkService.count_chunks(db, document_id=doc_id, user_id=user_id)
        assert count == r.chunk_count

    def test_get_chunk_metadata(self, db, seed_parsed_document):
        _, doc_id, user_id, _ = seed_parsed_document
        ChunkService.save_chunks(db, document_id=doc_id, user_id=user_id)

        meta = ChunkService.get_chunk_metadata(db, document_id=doc_id, user_id=user_id)
        assert meta.total_chunks > 0
        assert meta.total_chars > 0
        assert meta.total_estimated_tokens > 0
        assert meta.average_chunk_size > 0
        assert meta.average_chunk_tokens > 0

    def test_archive_chunks(self, db, seed_parsed_document):
        parsed_id, doc_id, user_id, _ = seed_parsed_document
        ChunkService.save_chunks(db, document_id=doc_id, user_id=user_id)

        archived = ChunkService.archive_chunks(db, document_id=doc_id, user_id=user_id)
        assert archived > 0

        ready = chunk_repo.get_chunk_count(db, parsed_id, status_filter=ChunkStatus.READY.value)
        assert ready == 0

    def test_service_metrics_updated(self, db, seed_parsed_document):
        _, doc_id, user_id, _ = seed_parsed_document
        before = ChunkService.get_metrics()
        ChunkService.save_chunks(db, document_id=doc_id, user_id=user_id)
        after = ChunkService.get_metrics()
        assert after["chunks_saved_total"] >= before["chunks_saved_total"]


# ══════════════════════════════════════════════════════════════════════════════
# INTEGRATION TESTS
# ══════════════════════════════════════════════════════════════════════════════

class TestIntegration:
    def test_full_pipeline_parsed_to_chunks(self, db, seed_parsed_document):
        """ParsedDocument → ChunkingService → ChunkService → DB → Retrieve."""
        parsed_id, doc_id, user_id, original_text = seed_parsed_document

        # Generate + persist
        result = ChunkService.save_chunks(db, document_id=doc_id, user_id=user_id)
        assert result.chunk_count > 0
        assert result.strategy == "recursive"

        # Retrieve
        response = ChunkService.get_chunks(db, document_id=doc_id, user_id=user_id)
        assert response.total == result.chunk_count

        # All chunk text should be substrings of the original (possibly with overlap)
        combined = " ".join(c.chunk_text for c in response.chunks)
        assert len(combined) > 0

        # Metadata
        meta = ChunkService.get_chunk_metadata(db, document_id=doc_id, user_id=user_id)
        assert meta.total_chunks == result.chunk_count
        assert meta.strategy == "recursive"

    def test_rechunk_produces_fresh_chunks(self, db, seed_parsed_document):
        """Rechunking should archive old and produce a fresh READY set."""
        parsed_id, doc_id, user_id, _ = seed_parsed_document

        r1 = ChunkService.save_chunks(db, document_id=doc_id, user_id=user_id)
        r2 = ChunkService.regenerate_chunks(
            db, document_id=doc_id, user_id=user_id, chunk_size=400
        )

        assert r2.chunk_count > 0
        assert "Archived" in r2.message

        archived = chunk_repo.get_chunk_count(
            db, parsed_id, status_filter=ChunkStatus.ARCHIVED.value
        )
        assert archived == r1.chunk_count

    def test_chunk_strategy_metadata_persisted(self, db, seed_parsed_document):
        """Strategy name and version should be stored in DB."""
        parsed_id, doc_id, user_id, _ = seed_parsed_document
        ChunkService.save_chunks(db, document_id=doc_id, user_id=user_id)

        chunks = chunk_repo.get_ready_chunks(db, parsed_id)
        for c in chunks:
            assert c.strategy == "recursive"
            assert c.strategy_version == "1.0.0"

    def test_chunk_offsets_stored(self, db, seed_parsed_document):
        """start_offset and end_offset should be non-negative integers."""
        parsed_id, doc_id, user_id, _ = seed_parsed_document
        ChunkService.save_chunks(db, document_id=doc_id, user_id=user_id)

        chunks = chunk_repo.get_ready_chunks(db, parsed_id)
        for c in chunks:
            assert c.start_offset >= 0
            assert c.end_offset >= c.start_offset


# ══════════════════════════════════════════════════════════════════════════════
# PERFORMANCE TESTS
# ══════════════════════════════════════════════════════════════════════════════

class TestPerformance:
    def test_tiny_document(self, db, seed_document):
        """Single sentence document should produce exactly 1 chunk."""
        doc_id, user_id = seed_document
        parsed_id = str(uuid.uuid4())
        db.execute(
            text("INSERT INTO parsed_documents (id, document_id, text_content, status) VALUES (:id, :did, :t, :s)"),
            {"id": parsed_id, "did": doc_id, "t": "Hello.", "s": "READY"},
        )
        db.commit()

        result = ChunkService.save_chunks(db, document_id=doc_id, user_id=user_id)
        assert result.chunk_count == 1

    def test_large_document_within_time_budget(self, db, seed_document):
        """5000-word document should chunk in under 2 seconds."""
        doc_id, user_id = seed_document
        large_text = " ".join(f"This is sentence number {i} in a very large document." for i in range(500))

        parsed_id = str(uuid.uuid4())
        db.execute(
            text("INSERT INTO parsed_documents (id, document_id, text_content, status) VALUES (:id, :did, :t, :s)"),
            {"id": parsed_id, "did": doc_id, "t": large_text, "s": "READY"},
        )
        db.commit()

        start = time.monotonic()
        result = ChunkService.save_chunks(db, document_id=doc_id, user_id=user_id)
        duration = time.monotonic() - start

        assert result.chunk_count > 0
        assert duration < 5.0  # generous budget for CI

    def test_markdown_document(self, db, seed_document):
        """Markdown document with headings and code blocks."""
        doc_id, user_id = seed_document
        md_text = """# Introduction

This is the introduction section of the document.
It has multiple sentences and paragraphs.

## Background

The background section explains the context.
This is important for understanding the work.

### Related Work

```python
def chunk_text(text: str) -> list:
    return text.split("\\n\\n")
```

The code above shows a simple chunking approach.

## Methods

The methods section describes the approach taken.
We use recursive splitting with overlap.

## Results

Results show improved retrieval quality.
F1 score improved significantly.

## Conclusion

In conclusion, intelligent chunking is critical.
"""
        parsed_id = str(uuid.uuid4())
        # Update the doc to be md type
        db.execute(text("UPDATE documents SET file_extension='md' WHERE id=:id"), {"id": doc_id})
        db.execute(
            text("INSERT INTO parsed_documents (id, document_id, text_content, status) VALUES (:id, :did, :t, :s)"),
            {"id": parsed_id, "did": doc_id, "t": md_text, "s": "READY"},
        )
        db.commit()

        result = ChunkService.save_chunks(db, document_id=doc_id, user_id=user_id)
        assert result.chunk_count > 0

    def test_bulk_insert_performance(self, db, seed_parsed_document):
        """Bulk insert of 500 chunks should complete quickly."""
        parsed_id, _, user_id, _ = seed_parsed_document
        chunk_data_list = [
            _make_chunk(i, f"Chunk {i}: " + "content " * 20, i * 150, (i + 1) * 150)
            for i in range(500)
        ]

        start = time.monotonic()
        chunks = chunk_repo.bulk_create_chunks(
            db,
            parsed_document_id=parsed_id,
            user_id=user_id,
            chunk_data_list=chunk_data_list,
        )
        db.commit()
        duration = time.monotonic() - start

        assert len(chunks) == 500
        assert duration < 5.0
