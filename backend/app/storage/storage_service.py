"""
StorageService — business-facing facade for the Storage Layer (Day 66 Part A2).

Responsibilities:
    - Delegate all IO to the configured StorageProvider.
    - Normalise provider responses into consistent return types.
    - Add structured logging for every operation.
    - Track upload/download/delete metrics (lightweight counters).
    - Translate StorageError subtypes into FastAPI HTTPExceptions
      when called from within an HTTP request context.

The rest of the application (DocumentService, future parser, RAG retriever)
communicates ONLY with StorageService — never with a concrete provider.

Dependency injection:
    StorageService is instantiated once at module level using the
    provider selected by StorageProviderFactory.  Tests can swap the
    provider by calling StorageService(provider=FakeProvider()).
"""
from __future__ import annotations

import logging
import time
from typing import AsyncGenerator

from fastapi import HTTPException, status

from app.exceptions.storage_exceptions import (
    StorageDeleteError,
    StorageReadError,
    StorageUnavailable,
    StorageValidationError,
    StorageWriteError,
)
from app.storage.storage_factory import StorageProviderFactory
from app.storage.storage_provider import StorageMetadata, StorageProvider

logger = logging.getLogger(__name__)

# ── Lightweight metrics ───────────────────────────────────────────────────────
_metrics: dict[str, int | float] = {
    "uploads_total": 0,
    "uploads_failed": 0,
    "downloads_total": 0,
    "downloads_failed": 0,
    "deletes_total": 0,
    "deletes_failed": 0,
    "total_bytes_uploaded": 0,
    "total_upload_latency_ms": 0.0,
}


def get_storage_metrics() -> dict:
    """Return a copy of current storage metrics."""
    return dict(_metrics)


class StorageService:
    """
    Facade over any :class:`StorageProvider` implementation.

    Args:
        provider: Optional explicit provider (useful in tests).
                  If None, the factory creates the configured default.
    """

    def __init__(self, provider: StorageProvider | None = None) -> None:
        self._provider: StorageProvider = provider or StorageProviderFactory.get_provider()
        logger.info(
            "StorageService initialised with provider: %s",
            type(self._provider).__name__,
        )

    # ── Save ─────────────────────────────────────────────────────────────────

    def save_file(
        self,
        file_data: bytes,
        user_id: int,
        document_id: str,
        extension: str,
    ) -> StorageMetadata:
        """
        Persist a file and return its metadata.

        Args:
            file_data:   Raw file bytes.
            user_id:     Owner's user ID.
            document_id: Document UUID string.
            extension:   Lowercase extension without dot.

        Returns:
            :class:`StorageMetadata` with path, filename, size, checksum.

        Raises:
            HTTPException 503: Storage provider unavailable.
            HTTPException 500: Write error or unexpected failure.
        """
        logger.info(
            "StorageService.save_file — user_id=%d document_id=%s size=%d",
            user_id,
            document_id,
            len(file_data),
        )
        t0 = time.monotonic()

        try:
            metadata = self._provider.save_file(
                file_data=file_data,
                user_id=user_id,
                document_id=document_id,
                extension=extension,
            )
        except StorageUnavailable as exc:
            _metrics["uploads_failed"] += 1
            logger.error("Storage unavailable during save: %s", exc)
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Storage service is currently unavailable. Try again later.",
            )
        except StorageWriteError as exc:
            _metrics["uploads_failed"] += 1
            logger.error("Storage write error: %s", exc)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to store the uploaded file. Please try again.",
            )
        except StorageValidationError as exc:
            _metrics["uploads_failed"] += 1
            logger.error("Storage validation error during save: %s", exc)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(exc),
            )

        elapsed_ms = (time.monotonic() - t0) * 1000
        _metrics["uploads_total"] += 1
        _metrics["total_bytes_uploaded"] += metadata.size
        _metrics["total_upload_latency_ms"] += elapsed_ms

        logger.info(
            "StorageService.save_file complete — path=%s size=%d checksum=%s latency=%.1fms",
            metadata.storage_path,
            metadata.size,
            metadata.checksum,
            elapsed_ms,
        )
        return metadata

    # ── Get (full read) ──────────────────────────────────────────────────────

    def get_file(self, storage_path: str) -> bytes:
        """
        Read and return the entire file content as bytes.

        Args:
            storage_path: Provider-relative path (from document metadata).

        Returns:
            Raw file bytes.

        Raises:
            HTTPException 404: File not found in storage.
            HTTPException 500: Read error.
        """
        logger.info("StorageService.get_file — path=%s", storage_path)
        _metrics["downloads_total"] += 1

        try:
            return self._provider.get_file(storage_path)
        except StorageReadError as exc:
            _metrics["downloads_failed"] += 1
            logger.error("Storage read error during get_file: %s", exc)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document file not found in storage.",
            )

    # ── Stream ───────────────────────────────────────────────────────────────

    async def stream_file(
        self,
        storage_path: str,
        chunk_size: int = 65_536,
    ) -> AsyncGenerator[bytes, None]:
        """
        Stream a file for download using an async generator.

        Args:
            storage_path: Provider-relative path (from document metadata).
            chunk_size:   Bytes per chunk (default 64 KB).

        Yields:
            Byte chunks suitable for FastAPI ``StreamingResponse``.

        Raises:
            HTTPException 404: File not found in storage.
            HTTPException 500: Read / stream error.
        """
        logger.info(
            "StorageService.stream_file — path=%s chunk_size=%d",
            storage_path,
            chunk_size,
        )
        _metrics["downloads_total"] += 1

        try:
            async for chunk in self._provider.stream_file(storage_path, chunk_size):
                yield chunk
        except StorageReadError as exc:
            _metrics["downloads_failed"] += 1
            logger.error("Storage read error during stream: %s", exc)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document file not found in storage.",
            )

    # ── Delete ───────────────────────────────────────────────────────────────

    def delete_file(self, storage_path: str) -> bool:
        """
        Delete a file from storage.

        Args:
            storage_path: Provider-relative path.

        Returns:
            True if deleted, False if the file did not exist.

        Raises:
            HTTPException 500: Deletion failed.
        """
        logger.info("StorageService.delete_file — path=%s", storage_path)

        try:
            deleted = self._provider.delete_file(storage_path)
        except StorageDeleteError as exc:
            _metrics["deletes_failed"] += 1
            logger.error("Storage delete error: %s", exc)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete the document file from storage.",
            )

        _metrics["deletes_total"] += 1
        logger.info(
            "StorageService.delete_file complete — path=%s deleted=%s",
            storage_path,
            deleted,
        )
        return deleted

    # ── Exists / Metadata ─────────────────────────────────────────────────────

    def file_exists(self, storage_path: str) -> bool:
        """Check whether a file exists at the given provider-relative path."""
        return self._provider.exists(storage_path)

    def get_file_metadata(self, storage_path: str) -> StorageMetadata:
        """Return file metadata (size, existence) without reading content."""
        return self._provider.get_file_metadata(storage_path)

    def generate_storage_path(
        self,
        user_id: int,
        document_id: str,
        extension: str,
    ) -> str:
        """Compute the provider-relative storage path without creating any files."""
        return self._provider.generate_storage_path(user_id, document_id, extension)

    def validate_file_integrity(
        self,
        storage_path: str,
        expected_size: int,
        expected_checksum: str | None = None,
    ) -> bool:
        """
        Verify that a stored file matches its recorded metadata.

        Args:
            storage_path:      Provider-relative path.
            expected_size:     Size in bytes as recorded in the database.
            expected_checksum: SHA-256 hex digest as recorded in the database (optional).

        Returns:
            True if all checks pass, False if any discrepancy is detected.
        """
        meta = self.get_file_metadata(storage_path)
        if not meta.exists:
            logger.warning("Integrity check failed — file missing: %s", storage_path)
            return False
        if meta.size != expected_size:
            logger.warning(
                "Integrity check failed — size mismatch: expected=%d actual=%d path=%s",
                expected_size,
                meta.size,
                storage_path,
            )
            return False
        # Checksum validation (only if checksum is explicitly requested)
        if expected_checksum:
            from app.utils.checksum import calculate_sha256
            try:
                file_bytes = self._provider.get_file(storage_path)
                actual_checksum = calculate_sha256(file_bytes)
                if actual_checksum != expected_checksum:
                    logger.warning(
                        "Integrity check failed — checksum mismatch: path=%s",
                        storage_path,
                    )
                    return False
            except StorageReadError:
                return False
        return True

    @property
    def provider(self) -> StorageProvider:
        """Expose the underlying provider (needed by health + cleanup services)."""
        return self._provider


# ── Module-level singleton ────────────────────────────────────────────────────
# Created once at import time.  Tests can replace it via dependency injection.
storage_service = StorageService()
