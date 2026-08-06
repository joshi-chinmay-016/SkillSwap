"""
LocalStorageProvider — Filesystem implementation of StorageProvider (Day 66 Part A2).

Responsibilities:
    - Save uploaded files to a configurable local directory.
    - Create per-user subdirectories automatically.
    - Generate UUID-based stored filenames (prevents filename attacks).
    - Stream downloads to avoid loading large files into memory.
    - Validate paths against directory traversal attacks.
    - Handle all IO errors and wrap them in typed StorageError subclasses.

Directory layout:
    {UPLOAD_DIRECTORY}/
        {user_id}/
            {document_uuid}.{ext}

Example:
    uploads/
        42/
            e43dd4bb-acde-46ab-beef-aabbccddeeff.pdf

This is the DEFAULT provider.  Replacing it with S3 or Azure requires only:
    1. Set STORAGE_PROVIDER=S3 in .env.
    2. Implement S3StorageProvider (future Day 66+ work).
"""
from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import AsyncGenerator

from app.exceptions.storage_exceptions import (
    StorageDeleteError,
    StorageReadError,
    StorageUnavailable,
    StorageValidationError,
    StorageWriteError,
)
from app.storage.storage_provider import StorageMetadata, StorageProvider
from app.utils.checksum import calculate_sha256

logger = logging.getLogger(__name__)


class LocalStorageProvider(StorageProvider):
    """
    Filesystem-backed storage provider.

    Args:
        base_directory: Absolute or relative path to the upload root.
                        The directory is created on first use if it does not exist.
    """

    def __init__(self, base_directory: str) -> None:
        self._base = Path(base_directory).resolve()
        logger.info("LocalStorageProvider initialised — base: %s", self._base)

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _resolve_path(self, storage_path: str) -> Path:
        """
        Resolve a provider-relative ``storage_path`` to an absolute filesystem path
        and verify it does not escape the base directory (path traversal guard).

        Args:
            storage_path: Provider-relative path (e.g. ``uploads/42/uuid.pdf``).

        Returns:
            Absolute :class:`pathlib.Path`.

        Raises:
            StorageValidationError: If the resolved path escapes the base directory.
        """
        # storage_path may begin with the directory prefix or just be a relative path
        resolved = (self._base / storage_path).resolve()

        # Strict parent-check — prevents ../../etc/passwd style paths
        try:
            resolved.relative_to(self._base)
        except ValueError:
            logger.warning(
                "Path traversal attempt detected: storage_path=%r resolved=%s base=%s",
                storage_path,
                resolved,
                self._base,
            )
            raise StorageValidationError(
                f"Path traversal detected in storage_path: '{storage_path}'"
            )

        return resolved

    def _ensure_user_directory(self, user_id: int) -> Path:
        """
        Create ``{base}/{user_id}/`` if it does not exist.

        Args:
            user_id: Owner's user ID.

        Returns:
            Absolute path to the per-user directory.

        Raises:
            StorageUnavailable: If the directory cannot be created.
        """
        user_dir = self._base / str(user_id)
        try:
            user_dir.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            logger.error(
                "Cannot create upload directory for user %d: %s", user_id, exc
            )
            raise StorageUnavailable(
                f"Cannot create storage directory for user {user_id}.",
                cause=exc,
            )
        return user_dir

    # ── StorageProvider implementation ────────────────────────────────────────

    def generate_storage_path(
        self,
        user_id: int,
        document_id: str,
        extension: str,
    ) -> str:
        """
        Compute the provider-relative path WITHOUT creating any files.

        Returns a forward-slash path for portability and consistent
        database storage across operating systems.
        """
        return f"{user_id}/{document_id}.{extension}"

    def save_file(
        self,
        file_data: bytes,
        user_id: int,
        document_id: str,
        extension: str,
    ) -> StorageMetadata:
        """
        Write ``file_data`` to ``{base}/{user_id}/{document_id}.{extension}``.

        Steps:
            1. Ensure per-user directory exists.
            2. Compute the storage path.
            3. Validate path (traversal guard).
            4. Write atomically (temp file → rename is not used here because
               UUID filenames already guarantee uniqueness; a partial write
               will simply be cleaned up by StorageCleanupService).
            5. Calculate and return checksum.

        Returns:
            :class:`StorageMetadata` populated with path, filename, size, checksum.
        """
        user_dir = self._ensure_user_directory(user_id)
        relative_path = self.generate_storage_path(user_id, document_id, extension)
        abs_path = self._resolve_path(relative_path)

        logger.debug(
            "Saving file — user_id=%d document_id=%s size=%d bytes path=%s",
            user_id,
            document_id,
            len(file_data),
            abs_path,
        )

        try:
            abs_path.write_bytes(file_data)
        except OSError as exc:
            logger.error("Write failed: %s — %s", abs_path, exc)
            raise StorageWriteError(
                f"Failed to write file '{document_id}.{extension}' to storage.",
                cause=exc,
            )

        checksum = calculate_sha256(file_data)
        size = abs_path.stat().st_size
        stored_filename = f"{document_id}.{extension}"

        logger.info(
            "File saved — stored_filename=%s size=%d checksum=%s",
            stored_filename,
            size,
            checksum,
        )

        return StorageMetadata(
            storage_path=relative_path,
            stored_filename=stored_filename,
            size=size,
            exists=True,
            checksum=checksum,
        )

    def get_file(self, storage_path: str) -> bytes:
        """
        Read and return the entire file as bytes.

        Suitable for small files.  For large files use :meth:`stream_file`.
        """
        abs_path = self._resolve_path(storage_path)

        if not abs_path.exists():
            raise StorageReadError(
                f"File not found at storage path: '{storage_path}'"
            )

        try:
            return abs_path.read_bytes()
        except OSError as exc:
            logger.error("Read failed: %s — %s", abs_path, exc)
            raise StorageReadError(
                f"Failed to read file at '{storage_path}'.",
                cause=exc,
            )

    async def stream_file(
        self, storage_path: str, chunk_size: int = 65_536
    ) -> AsyncGenerator[bytes, None]:
        """
        Async generator that yields the file in chunks.

        Avoids loading the entire file into memory — important for PDFs.
        Compatible with FastAPI's ``StreamingResponse``.
        """
        abs_path = self._resolve_path(storage_path)

        if not abs_path.exists():
            raise StorageReadError(
                f"File not found at storage path: '{storage_path}'"
            )

        try:
            with abs_path.open("rb") as fh:
                while True:
                    chunk = fh.read(chunk_size)
                    if not chunk:
                        break
                    yield chunk
        except OSError as exc:
            logger.error("Stream failed: %s — %s", abs_path, exc)
            raise StorageReadError(
                f"Failed to stream file at '{storage_path}'.",
                cause=exc,
            )

    def get_file_metadata(self, storage_path: str) -> StorageMetadata:
        """Return size and existence info without reading the file content."""
        abs_path = self._resolve_path(storage_path)
        exists = abs_path.exists()
        size = abs_path.stat().st_size if exists else 0
        stored_filename = abs_path.name

        return StorageMetadata(
            storage_path=storage_path,
            stored_filename=stored_filename,
            size=size,
            exists=exists,
        )

    def exists(self, storage_path: str) -> bool:
        """Check whether a file exists at the given provider-relative path."""
        try:
            abs_path = self._resolve_path(storage_path)
            return abs_path.exists()
        except StorageValidationError:
            return False

    def delete_file(self, storage_path: str) -> bool:
        """
        Remove the file at ``storage_path``.

        Returns:
            True if deleted, False if the file did not exist.

        Raises:
            StorageDeleteError: On OS-level deletion failure.
        """
        abs_path = self._resolve_path(storage_path)

        if not abs_path.exists():
            logger.warning("Delete: file not found — %s (no-op)", abs_path)
            return False

        try:
            abs_path.unlink()
            logger.info("File deleted — %s", abs_path)
            return True
        except OSError as exc:
            logger.error("Delete failed: %s — %s", abs_path, exc)
            raise StorageDeleteError(
                f"Failed to delete file at '{storage_path}'.",
                cause=exc,
            )

    # ── Extra helpers exposed for health / cleanup services ───────────────────

    @property
    def base_directory(self) -> Path:
        """Absolute base directory path."""
        return self._base

    def list_user_files(self, user_id: int) -> list[str]:
        """
        Return a list of provider-relative paths for all files owned by ``user_id``.

        Used by :class:`StorageCleanupService`.
        """
        user_dir = self._base / str(user_id)
        if not user_dir.exists():
            return []
        return [
            f"{user_id}/{f.name}"
            for f in user_dir.iterdir()
            if f.is_file()
        ]

    def list_all_files(self) -> list[str]:
        """
        Walk the entire base directory and return all provider-relative paths.

        Used by :class:`StorageCleanupService` for orphan detection.
        """
        results: list[str] = []
        if not self._base.exists():
            return results
        for user_dir in self._base.iterdir():
            if user_dir.is_dir():
                for f in user_dir.iterdir():
                    if f.is_file():
                        results.append(f"{user_dir.name}/{f.name}")
        return results
