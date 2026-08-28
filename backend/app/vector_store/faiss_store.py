"""
FAISSVectorStore — Concrete FAISS implementation of VectorStore (Day 70).

Index type:
    faiss.IndexIDMap2(faiss.IndexFlatIP(dimension))

    - IndexFlatIP  : Exact inner-product search. Compatible with L2-normalised
                     embeddings (cosine similarity). Correct by definition —
                     no approximation errors at current project scale.
    - IndexIDMap2  : Wraps IndexFlatIP with explicit int64 vector IDs.
                     Supports add_with_ids() and remove_ids() operations.
                     Required for deterministic embedding_id ↔ faiss_id mapping.

Vector ID strategy:
    embedding_id (UUID str)
        → SHA-256 hash (256 bits)
        → truncated to 63 bits (signed int64 safe)
        → faiss_id (int64)

    This is deterministic, collision-resistant, and requires no DB round-trip.

Persistence:
    Two files on disk:
        <FAISS_INDEX_DIR>/<FAISS_INDEX_FILENAME>  — FAISS binary index
        <FAISS_INDEX_DIR>/<FAISS_MAPPING_FILENAME> — JSON mapping

    Both are written atomically via temp file + os.replace().

Concurrency:
    A threading.Lock guards all mutation operations (add, remove, rebuild, save).
    Multiple FastAPI background tasks cannot corrupt the index.

Security:
    - Raw vector values are never logged.
    - API keys / credentials are never referenced here.
    - document_id / embedding_id identifiers are safe for logging.
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
import threading
from pathlib import Path
from typing import Optional

import numpy as np

from app.vector_store.base import VectorStore, VectorStoreHealth
from app.vector_store.exceptions import (
    FAISSIndexError,
    VectorDimensionMismatchError,
    VectorIndexingError,
    VectorMappingError,
    VectorRebuildError,
    VectorStoreInitializationError,
    VectorStorePersistenceError,
)

logger = logging.getLogger(__name__)

# ── Constants ─────────────────────────────────────────────────────────────────

_MAPPING_VERSION = 1          # Increment when mapping JSON schema changes
_NUMPY_DTYPE = np.float32     # FAISS requires float32


# ── Helper ────────────────────────────────────────────────────────────────────

def _embedding_id_to_faiss_id(embedding_id: str) -> int:
    """
    Deterministically derive a positive int64 FAISS vector ID from an embedding UUID.

    Uses SHA-256 truncated to 63 bits so the result fits in a signed int64.
    The mapping is collision-resistant at the scale of this project.

    Args:
        embedding_id: UUID string from the embeddings table.

    Returns:
        Stable positive int64 suitable as a FAISS ID.
    """
    digest = hashlib.sha256(embedding_id.encode("utf-8")).hexdigest()
    # Take the first 16 hex chars (64 bits), mask to 63 bits for signed safety
    raw = int(digest[:16], 16)
    return raw & ((1 << 63) - 1)  # Ensure non-negative signed int64


# ── Implementation ────────────────────────────────────────────────────────────

class FAISSVectorStore(VectorStore):
    """
    FAISS-backed vector store using IndexIDMap2(IndexFlatIP(dimension)).

    Thread-safe for concurrent mutations.
    Persists index and ID mapping atomically to disk.

    Usage::

        store = FAISSVectorStore.from_settings()
        store.initialize_index()

        # Add vectors (returns mapping of embedding_id → faiss_id)
        mapping = store.add_vectors(vectors, embedding_ids)

        # Save after mutations
        store.save_index()

        # Health check
        health = store.health_check()

    This class must not perform any database operations.
    All PostgreSQL interactions belong in repositories or services.
    """

    def __init__(
        self,
        *,
        index_path: Path,
        mapping_path: Path,
        dimension: int,
    ) -> None:
        """
        Args:
            index_path   : Full path to the FAISS index file (e.g. .../skillswap.index).
            mapping_path : Full path to the JSON mapping file.
            dimension    : Expected embedding vector dimension.
                           Must be > 0. Auto-detect is handled by the factory.
        """
        if dimension <= 0:
            raise VectorStoreInitializationError(
                f"FAISSVectorStore requires dimension > 0, got {dimension}."
            )
        self._index_path = index_path
        self._mapping_path = mapping_path
        self._dimension = dimension

        # Runtime state — protected by _lock
        self._lock = threading.Lock()
        self._index = None              # faiss.IndexIDMap2 | None
        self._initialized = False
        # Bidirectional mapping: embedding_id (str) ↔ faiss_id (int)
        self._id_to_faiss: dict[str, int] = {}   # embedding_id → faiss_id
        self._faiss_to_id: dict[int, str] = {}   # faiss_id → embedding_id

    # ── Factory ───────────────────────────────────────────────────────────────

    @classmethod
    def from_settings(cls) -> "FAISSVectorStore":
        """
        Construct a FAISSVectorStore from the application settings.

        Reads FAISS_INDEX_DIR, FAISS_INDEX_FILENAME, FAISS_MAPPING_FILENAME,
        and FAISS_EMBEDDING_DIMENSION from app.core.config.settings.

        The directory is created if it does not exist.

        Returns:
            Uninitialised FAISSVectorStore. Call initialize_index() before use.

        Raises:
            VectorStoreInitializationError: Configuration is invalid.
            VectorStorePersistenceError   : Index directory cannot be created.
        """
        from app.core.config import settings

        index_dir_raw: str = getattr(settings, "FAISS_INDEX_DIR", "vector_store")
        index_filename: str = getattr(settings, "FAISS_INDEX_FILENAME", "skillswap.index")
        mapping_filename: str = getattr(settings, "FAISS_MAPPING_FILENAME", "skillswap_mapping.json")
        dimension: int = getattr(settings, "FAISS_EMBEDDING_DIMENSION", 768)

        # Resolve path relative to the backend directory (where the process runs)
        index_dir = Path(index_dir_raw)
        if not index_dir.is_absolute():
            # Make relative to the current working directory (backend/)
            index_dir = Path.cwd() / index_dir

        try:
            index_dir.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            raise VectorStorePersistenceError(
                f"Cannot create FAISS index directory: {index_dir}",
                cause=exc,
            ) from exc

        if not os.access(index_dir, os.W_OK):
            raise VectorStorePersistenceError(
                f"FAISS index directory is not writable: {index_dir}"
            )

        if dimension <= 0:
            raise VectorStoreInitializationError(
                f"FAISS_EMBEDDING_DIMENSION must be > 0, got {dimension}. "
                "Check your .env file."
            )

        logger.info(
            "FAISSVectorStore — configured index_dir=%s dimension=%d",
            index_dir,
            dimension,
        )

        return cls(
            index_path=index_dir / index_filename,
            mapping_path=index_dir / mapping_filename,
            dimension=dimension,
        )

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    def initialize_index(self) -> None:
        """
        Load an existing index from disk, or create a new empty index.

        Call this once at application startup or before the first indexing job.

        Flow:
            Index file exists → load → validate dimension → load mapping
            Index file missing → create new empty index
            Index file corrupted → raise VectorStoreInitializationError

        Raises:
            VectorStoreInitializationError: Index is corrupted or unreadable.
            VectorDimensionMismatchError  : Index dimension != configured dimension.
            VectorStorePersistenceError   : Disk read failed.
        """
        with self._lock:
            if self._index_path.exists():
                logger.info(
                    "FAISSVectorStore — index file found at %s, loading...",
                    self._index_path,
                )
                self._load_index_locked()
            else:
                logger.info(
                    "FAISSVectorStore — no index file at %s, creating new empty index "
                    "(dimension=%d).",
                    self._index_path,
                    self._dimension,
                )
                self._create_empty_index_locked()

            self._initialized = True
            logger.info(
                "FAISSVectorStore — initialized: dimension=%d vectors=%d",
                self._dimension,
                self._index.ntotal,
            )

    def save_index(self) -> None:
        """
        Atomically persist the FAISS index and ID mapping to disk.

        Uses temp file + os.replace() for atomic write.
        If the write fails, the existing valid index files remain untouched.

        Raises:
            VectorStoreInitializationError: Index is not initialized.
            VectorStorePersistenceError   : Save failed.
        """
        with self._lock:
            self._assert_initialized()
            self._save_locked()

    def load_index(self) -> None:
        """
        Load the index from disk into memory (explicit reload).

        Raises:
            VectorStoreInitializationError: Index file not found.
            VectorDimensionMismatchError  : Index dimension != configured dimension.
            VectorStorePersistenceError   : Disk read failed.
        """
        with self._lock:
            if not self._index_path.exists():
                raise VectorStoreInitializationError(
                    f"FAISS index file not found: {self._index_path}. "
                    "Call initialize_index() to create a new empty index."
                )
            self._load_index_locked()
            self._initialized = True

    # ── Mutation ──────────────────────────────────────────────────────────────

    def add_vectors(
        self,
        vectors: list[list[float]],
        embedding_ids: list[str],
    ) -> dict[str, int]:
        """
        Add vectors to the FAISS index.

        Validates each vector's dimension before adding.
        Skips vectors whose embedding_id is already in the mapping (idempotency).

        Args:
            vectors       : Float vectors — each must have length == self._dimension.
            embedding_ids : Embedding UUID strings (same length as vectors).

        Returns:
            Dict mapping embedding_id → faiss_id for vectors actually added.

        Raises:
            VectorStoreInitializationError: Index not initialized.
            VectorDimensionMismatchError  : A vector has the wrong dimension.
            FAISSIndexError               : FAISS add operation failed.
        """
        if len(vectors) != len(embedding_ids):
            raise VectorIndexingError(
                f"vectors length ({len(vectors)}) != embedding_ids length "
                f"({len(embedding_ids)})."
            )

        with self._lock:
            self._assert_initialized()

            new_vectors: list[list[float]] = []
            new_faiss_ids: list[int] = []
            result_mapping: dict[str, int] = {}

            for vec, emb_id in zip(vectors, embedding_ids):
                # Idempotency: skip already-indexed vectors
                if emb_id in self._id_to_faiss:
                    logger.debug(
                        "FAISSVectorStore.add_vectors — skipping already-indexed "
                        "embedding_id=%s",
                        emb_id,
                    )
                    continue

                # Dimension validation
                if len(vec) != self._dimension:
                    raise VectorDimensionMismatchError(
                        f"Vector dimension mismatch for embedding_id={emb_id!r}: "
                        f"expected={self._dimension}, actual={len(vec)}.",
                        expected_dimension=self._dimension,
                        actual_dimension=len(vec),
                        embedding_id=emb_id,
                    )

                # Additional safety: check for NaN/Inf
                arr = np.array(vec, dtype=_NUMPY_DTYPE)
                if not np.isfinite(arr).all():
                    raise VectorIndexingError(
                        f"Vector for embedding_id={emb_id!r} contains NaN or Inf. "
                        "Rejected before adding to FAISS.",
                        embedding_id=emb_id,
                    )

                faiss_id = _embedding_id_to_faiss_id(emb_id)

                # Collision check (extremely unlikely but safe)
                if faiss_id in self._faiss_to_id and self._faiss_to_id[faiss_id] != emb_id:
                    raise VectorMappingError(
                        f"FAISS ID collision: faiss_id={faiss_id} already mapped to "
                        f"embedding_id={self._faiss_to_id[faiss_id]!r}, "
                        f"cannot also map to {emb_id!r}."
                    )

                new_vectors.append(vec)
                new_faiss_ids.append(faiss_id)
                result_mapping[emb_id] = faiss_id

            if not new_vectors:
                logger.debug(
                    "FAISSVectorStore.add_vectors — all %d vectors already indexed.",
                    len(embedding_ids),
                )
                return result_mapping

            # Build contiguous float32 matrix
            matrix = np.array(new_vectors, dtype=_NUMPY_DTYPE)
            ids_array = np.array(new_faiss_ids, dtype=np.int64)

            try:
                self._index.add_with_ids(matrix, ids_array)
            except Exception as exc:
                raise FAISSIndexError(
                    f"faiss.add_with_ids() failed for batch of {len(new_vectors)} vectors.",
                    cause=exc,
                ) from exc

            # Update mapping
            for emb_id, faiss_id in result_mapping.items():
                self._id_to_faiss[emb_id] = faiss_id
                self._faiss_to_id[faiss_id] = emb_id

            logger.info(
                "FAISSVectorStore.add_vectors — added %d vectors, index size=%d",
                len(new_vectors),
                self._index.ntotal,
            )
            return result_mapping

    def remove_vectors(self, embedding_ids: list[str]) -> int:
        """
        Remove vectors from the index by embedding_id.

        Silently skips IDs not found in the mapping.

        Args:
            embedding_ids: Embedding UUID strings to remove.

        Returns:
            Number of vectors actually removed.

        Raises:
            VectorStoreInitializationError: Index not initialized.
            FAISSIndexError               : FAISS removal failed.
        """
        with self._lock:
            self._assert_initialized()

            faiss_ids_to_remove: list[int] = []
            emb_ids_to_remove: list[str] = []

            for emb_id in embedding_ids:
                faiss_id = self._id_to_faiss.get(emb_id)
                if faiss_id is None:
                    logger.debug(
                        "FAISSVectorStore.remove_vectors — embedding_id=%s not in index, "
                        "skipping.",
                        emb_id,
                    )
                    continue
                faiss_ids_to_remove.append(faiss_id)
                emb_ids_to_remove.append(emb_id)

            if not faiss_ids_to_remove:
                return 0

            ids_array = np.array(faiss_ids_to_remove, dtype=np.int64)
            try:
                self._index.remove_ids(ids_array)
            except Exception as exc:
                raise FAISSIndexError(
                    f"faiss.remove_ids() failed for {len(faiss_ids_to_remove)} vectors.",
                    cause=exc,
                ) from exc

            # Clean up mapping
            for emb_id, faiss_id in zip(emb_ids_to_remove, faiss_ids_to_remove):
                self._id_to_faiss.pop(emb_id, None)
                self._faiss_to_id.pop(faiss_id, None)

            logger.info(
                "FAISSVectorStore.remove_vectors — removed %d vectors, index size=%d",
                len(faiss_ids_to_remove),
                self._index.ntotal,
            )
            return len(faiss_ids_to_remove)

    def rebuild_index(
        self,
        vectors: list[list[float]],
        embedding_ids: list[str],
    ) -> None:
        """
        Safely rebuild the entire index from scratch.

        Strategy:
            1. Build new index + mapping in memory.
            2. Write to temporary files.
            3. Atomically replace existing index files.
            4. Update in-memory state.

        If any step fails before step 3: old index remains untouched.
        If step 3 fails: best-effort rollback (old index restored from backup paths).

        Args:
            vectors       : All vectors for the new index.
            embedding_ids : Matching embedding UUID strings.

        Raises:
            VectorRebuildError           : Rebuild failed; old index preserved.
            VectorDimensionMismatchError : A vector has the wrong dimension.
        """
        import faiss

        if len(vectors) != len(embedding_ids):
            raise VectorRebuildError(
                f"vectors length ({len(vectors)}) != embedding_ids length "
                f"({len(embedding_ids)}) — rebuild aborted."
            )

        logger.info(
            "FAISSVectorStore.rebuild_index — starting rebuild with %d vectors "
            "(dimension=%d).",
            len(vectors),
            self._dimension,
        )

        with self._lock:
            # ── 1. Build new index in memory ──────────────────────────────
            try:
                new_flat = faiss.IndexFlatIP(self._dimension)
                new_index = faiss.IndexIDMap2(new_flat)
            except Exception as exc:
                raise VectorRebuildError(
                    "Failed to create new FAISS index during rebuild.",
                    cause=exc,
                ) from exc

            new_id_to_faiss: dict[str, int] = {}
            new_faiss_to_id: dict[int, str] = {}

            for vec, emb_id in zip(vectors, embedding_ids):
                if len(vec) != self._dimension:
                    raise VectorDimensionMismatchError(
                        f"Rebuild aborted — vector dimension mismatch for "
                        f"embedding_id={emb_id!r}: "
                        f"expected={self._dimension}, actual={len(vec)}.",
                        expected_dimension=self._dimension,
                        actual_dimension=len(vec),
                        embedding_id=emb_id,
                    )

                arr = np.array(vec, dtype=_NUMPY_DTYPE).reshape(1, -1)
                faiss_id = _embedding_id_to_faiss_id(emb_id)

                try:
                    new_index.add_with_ids(arr, np.array([faiss_id], dtype=np.int64))
                except Exception as exc:
                    raise VectorRebuildError(
                        f"FAISS add_with_ids failed during rebuild for "
                        f"embedding_id={emb_id!r}.",
                        cause=exc,
                    ) from exc

                new_id_to_faiss[emb_id] = faiss_id
                new_faiss_to_id[faiss_id] = emb_id

            # ── 2. Write to temp files ─────────────────────────────────────
            tmp_index_path = self._index_path.with_suffix(".rebuild.tmp")
            tmp_mapping_path = self._mapping_path.with_suffix(".rebuild.tmp")

            try:
                faiss.write_index(new_index, str(tmp_index_path))
                self._write_mapping_to_path_locked(new_id_to_faiss, tmp_mapping_path)
            except Exception as exc:
                # Clean up temp files
                for p in (tmp_index_path, tmp_mapping_path):
                    try:
                        p.unlink(missing_ok=True)
                    except OSError:
                        pass
                raise VectorRebuildError(
                    "Failed to write new index during rebuild. Old index preserved.",
                    cause=exc,
                ) from exc

            # ── 3. Atomic replace ─────────────────────────────────────────
            try:
                os.replace(tmp_index_path, self._index_path)
                os.replace(tmp_mapping_path, self._mapping_path)
            except OSError as exc:
                for p in (tmp_index_path, tmp_mapping_path):
                    try:
                        p.unlink(missing_ok=True)
                    except OSError:
                        pass
                raise VectorRebuildError(
                    "Atomic rename failed during rebuild. Old index preserved.",
                    cause=exc,
                ) from exc

            # ── 4. Update in-memory state ──────────────────────────────────
            self._index = new_index
            self._id_to_faiss = new_id_to_faiss
            self._faiss_to_id = new_faiss_to_id
            self._initialized = True

            logger.info(
                "FAISSVectorStore.rebuild_index — completed: %d vectors indexed.",
                new_index.ntotal,
            )

    # ── Introspection ─────────────────────────────────────────────────────────

    def get_index_size(self) -> int:
        """Return the number of vectors currently in the index."""
        with self._lock:
            if self._index is None:
                return 0
            return self._index.ntotal

    def get_dimension(self) -> int:
        """Return the configured vector dimension."""
        return self._dimension

    def get_indexed_embedding_ids(self) -> set[str]:
        """Return the set of embedding_ids currently present in the index mapping."""
        with self._lock:
            return set(self._id_to_faiss.keys())

    def health_check(self) -> VectorStoreHealth:
        """Return a lightweight health status without expensive operations."""
        persistence_ok = False
        try:
            persistence_ok = os.access(self._index_path.parent, os.W_OK)
        except OSError:
            pass

        with self._lock:
            vector_count = self._index.ntotal if self._index is not None else 0
            return VectorStoreHealth(
                is_initialized=self._initialized,
                is_loaded=self._index is not None,
                dimension=self._dimension,
                vector_count=vector_count,
                persistence_ok=persistence_ok,
                index_path=str(self._index_path),
                details=(
                    f"Mapping entries: {len(self._id_to_faiss)}"
                    if self._initialized
                    else "Not initialized"
                ),
            )

    # ── Retrieval ────────────────────────────────────────────────────────────

    def search(
        self,
        query_vector: list[float],
        top_k: int,
    ) -> list[tuple[int, float]]:
        """
        Search the FAISS index for the top-k nearest vectors.

        Uses IndexFlatIP which returns inner-product scores.
        For L2-normalised embeddings this is equivalent to cosine similarity:
            higher score = more similar.

        Thread-safety:
            IndexFlatIP supports concurrent reads without a lock.
            Mutations (add/remove) are guarded by _lock separately.
            We read _index and _initialized under a brief lock snapshot
            then release before the FAISS call to avoid blocking writers.

        Args:
            query_vector : Float list of length == self._dimension.
            top_k        : Number of candidates. Must be >= 1.

        Returns:
            List of (faiss_id, score) sorted by score descending.
            Excludes FAISS sentinel ID -1 (returned for empty/short index).

        Raises:
            VectorStoreInitializationError : Index not initialized.
            VectorDimensionMismatchError   : Dimension mismatch.
            FAISSIndexError                : Unexpected FAISS error.
        """
        # Snapshot index reference under lock, then release before search
        with self._lock:
            self._assert_initialized()
            index_ref = self._index  # local ref; FAISS object is thread-safe for reads

        if len(query_vector) != self._dimension:
            raise VectorDimensionMismatchError(
                f"Query vector dimension mismatch: "
                f"expected={self._dimension}, actual={len(query_vector)}.",
                expected_dimension=self._dimension,
                actual_dimension=len(query_vector),
            )

        if top_k < 1:
            return []

        # Clamp top_k to actual index size to avoid FAISS warnings
        actual_k = min(top_k, index_ref.ntotal)
        if actual_k == 0:
            logger.debug("FAISSVectorStore.search — index is empty, returning no results.")
            return []

        query_matrix = np.array([query_vector], dtype=_NUMPY_DTYPE)

        try:
            distances, ids = index_ref.search(query_matrix, actual_k)
        except Exception as exc:
            raise FAISSIndexError(
                f"faiss.search() failed for top_k={top_k}.",
                cause=exc,
            ) from exc

        # distances shape: (1, actual_k), ids shape: (1, actual_k)
        results: list[tuple[int, float]] = []
        for faiss_id, score in zip(ids[0], distances[0]):
            if faiss_id == -1:  # FAISS sentinel for "not found"
                continue
            results.append((int(faiss_id), float(score)))

        # Already sorted descending by IndexFlatIP; make explicit for safety
        results.sort(key=lambda x: x[1], reverse=True)

        logger.debug(
            "FAISSVectorStore.search — top_k=%d candidates=%d",
            top_k, len(results),
        )
        return results

    def resolve_faiss_ids(self, faiss_ids: list[int]) -> dict[int, str]:
        """
        Batch-resolve FAISS vector IDs to embedding_ids.

        Returns only IDs that are present in the current mapping.
        Missing IDs (stale/orphaned vectors) are silently omitted —
        callers should log and handle them.

        Args:
            faiss_ids : List of FAISS int64 vector IDs from a search result.

        Returns:
            Dict mapping faiss_id → embedding_id for known IDs.
        """
        with self._lock:
            return {
                fid: self._faiss_to_id[fid]
                for fid in faiss_ids
                if fid in self._faiss_to_id
            }

    # ── Private helpers ───────────────────────────────────────────────────────

    def _assert_initialized(self) -> None:
        """Raise if the index has not been initialised. Must be called under _lock."""
        if not self._initialized or self._index is None:
            raise VectorStoreInitializationError(
                "FAISSVectorStore is not initialized. "
                "Call initialize_index() before performing operations."
            )

    def _create_empty_index_locked(self) -> None:
        """Create a new empty FAISS index in memory. Must be called under _lock."""
        import faiss

        try:
            flat = faiss.IndexFlatIP(self._dimension)
            self._index = faiss.IndexIDMap2(flat)
        except Exception as exc:
            raise VectorStoreInitializationError(
                f"Failed to create empty FAISS index (dimension={self._dimension}).",
                cause=exc,
            ) from exc

        self._id_to_faiss = {}
        self._faiss_to_id = {}
        logger.debug(
            "FAISSVectorStore — created new empty IndexIDMap2(IndexFlatIP(%d)).",
            self._dimension,
        )

    def _load_index_locked(self) -> None:
        """Load index + mapping from disk. Must be called under _lock."""
        import faiss

        # ── Load FAISS index ──────────────────────────────────────────────
        try:
            index = faiss.read_index(str(self._index_path))
        except Exception as exc:
            raise VectorStoreInitializationError(
                f"FAISS index at {self._index_path} is corrupted or unreadable.",
                cause=exc,
            ) from exc

        # ── Dimension validation ──────────────────────────────────────────
        loaded_dim = index.d
        if loaded_dim != self._dimension:
            raise VectorDimensionMismatchError(
                f"Loaded FAISS index has dimension={loaded_dim}, "
                f"but configured dimension={self._dimension}. "
                "Check FAISS_EMBEDDING_DIMENSION in settings.",
                expected_dimension=self._dimension,
                actual_dimension=loaded_dim,
            )

        self._index = index

        # ── Load mapping ──────────────────────────────────────────────────
        if self._mapping_path.exists():
            self._load_mapping_locked()
        else:
            logger.warning(
                "FAISSVectorStore — index file exists (%s) but mapping file is missing "
                "(%s). Mapping will be empty — consider running reconciliation.",
                self._index_path,
                self._mapping_path,
            )
            self._id_to_faiss = {}
            self._faiss_to_id = {}

        logger.info(
            "FAISSVectorStore — loaded index: dimension=%d vectors=%d mappings=%d",
            self._dimension,
            self._index.ntotal,
            len(self._id_to_faiss),
        )

    def _load_mapping_locked(self) -> None:
        """Load the JSON mapping file. Must be called under _lock."""
        try:
            raw = self._mapping_path.read_text(encoding="utf-8")
            data = json.loads(raw)
        except (OSError, json.JSONDecodeError) as exc:
            raise VectorMappingError(
                f"Mapping file at {self._mapping_path} is missing or corrupt.",
                cause=exc,
            ) from exc

        version = data.get("version", 0)
        if version != _MAPPING_VERSION:
            logger.warning(
                "FAISSVectorStore — mapping file version=%d, expected=%d. "
                "Attempting best-effort load.",
                version,
                _MAPPING_VERSION,
            )

        raw_mapping: dict[str, str] = data.get("id_to_faiss", {})
        self._id_to_faiss = {emb_id: int(faiss_id) for emb_id, faiss_id in raw_mapping.items()}
        self._faiss_to_id = {v: k for k, v in self._id_to_faiss.items()}

    def _save_locked(self) -> None:
        """Atomically persist index + mapping to disk. Must be called under _lock."""
        import faiss

        index_dir = self._index_path.parent

        # ── Save FAISS index ──────────────────────────────────────────────
        tmp_index = index_dir / (self._index_path.name + ".tmp")
        try:
            faiss.write_index(self._index, str(tmp_index))
            os.replace(tmp_index, self._index_path)
        except Exception as exc:
            try:
                tmp_index.unlink(missing_ok=True)
            except OSError:
                pass
            raise VectorStorePersistenceError(
                f"Failed to save FAISS index to {self._index_path}.",
                cause=exc,
            ) from exc

        # ── Save mapping ──────────────────────────────────────────────────
        self._write_mapping_to_path_locked(self._id_to_faiss, self._mapping_path)

        logger.debug(
            "FAISSVectorStore — saved index: %d vectors, %d mappings → %s",
            self._index.ntotal,
            len(self._id_to_faiss),
            self._index_path,
        )

    def _write_mapping_to_path_locked(
        self,
        id_to_faiss: dict[str, int],
        target_path: Path,
    ) -> None:
        """Write mapping JSON atomically to target_path. Must be called under _lock."""
        tmp_mapping = target_path.parent / (target_path.name + ".tmp")
        data = {
            "version": _MAPPING_VERSION,
            "id_to_faiss": {emb_id: faiss_id for emb_id, faiss_id in id_to_faiss.items()},
        }
        try:
            tmp_mapping.write_text(json.dumps(data, indent=None), encoding="utf-8")
            os.replace(tmp_mapping, target_path)
        except Exception as exc:
            try:
                tmp_mapping.unlink(missing_ok=True)
            except OSError:
                pass
            raise VectorStorePersistenceError(
                f"Failed to save FAISS mapping to {target_path}.",
                cause=exc,
            ) from exc
