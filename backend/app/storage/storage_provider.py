"""
StorageProvider — Abstract interface for all storage backends (Day 66 Part A2).

This contract is implemented by every storage backend:
    - LocalStorageProvider    (current — filesystem)
    - S3StorageProvider       (future)
    - AzureBlobStorageProvider (future)
    - GCSStorageProvider      (future)
    - MinIOStorageProvider    (future)

The rest of the application must ONLY depend on this interface,
never on a concrete implementation.

Changing from LOCAL to S3 requires only:
    1. Implement S3StorageProvider.
    2. Set STORAGE_PROVIDER=S3 in config.
    Zero changes to DocumentService, DocumentRouter, or any future parser.
"""
from __future__ import annotations

import abc
from dataclasses import dataclass, field
from typing import AsyncGenerator, Optional


@dataclass
class StorageMetadata:
    """
    Normalised metadata returned by every provider after a save or stat operation.

    Attributes:
        storage_path:    Provider-relative path  (e.g. ``uploads/42/uuid.pdf``).
        stored_filename: Filename only           (e.g. ``uuid.pdf``).
        size:            File size in bytes.
        exists:          Whether the file is confirmed present.
        checksum:        SHA-256 hex digest (empty string if not computed).
    """

    storage_path: str
    stored_filename: str
    size: int
    exists: bool
    checksum: str = field(default="")


class StorageProvider(abc.ABC):
    """
    Abstract base class — the contract every storage backend must fulfil.

    All methods that perform IO are **synchronous** in the base interface
    to keep the abstraction simple and compatible with the existing
    synchronous SQLAlchemy session pattern.  The LocalStorageProvider
    uses standard file IO.  Future async-native providers (e.g. S3 via
    aioboto3) can override with async implementations when the application
    migrates to fully async endpoints.

    Design rule: No storage-specific logic outside concrete implementations.
    """

    # ── Write ────────────────────────────────────────────────────────────────

    @abc.abstractmethod
    def save_file(
        self,
        file_data: bytes,
        user_id: int,
        document_id: str,
        extension: str,
    ) -> StorageMetadata:
        """
        Persist ``file_data`` and return metadata describing the stored file.

        Args:
            file_data:   Raw bytes of the uploaded file.
            user_id:     Owner's user ID (used for directory scoping).
            document_id: Document UUID (used as the stored filename stem).
            extension:   Lowercase file extension without dot (e.g. ``pdf``).

        Returns:
            :class:`StorageMetadata` with storage_path, stored_filename, size, checksum.

        Raises:
            StorageWriteError: If the file cannot be persisted.
            StorageUnavailable: If the provider is not reachable.
        """

    # ── Read ─────────────────────────────────────────────────────────────────

    @abc.abstractmethod
    def get_file(self, storage_path: str) -> bytes:
        """
        Retrieve the full file content as bytes.

        Prefer :meth:`stream_file` for large files to avoid loading
        the entire content into memory.

        Args:
            storage_path: Provider-relative path returned by :meth:`save_file`.

        Returns:
            Raw bytes of the file.

        Raises:
            StorageReadError: If the file cannot be read.
        """

    @abc.abstractmethod
    def stream_file(self, storage_path: str, chunk_size: int = 65_536) -> AsyncGenerator[bytes, None]:
        """
        Stream file content in chunks, suitable for HTTP streaming responses.

        Args:
            storage_path: Provider-relative path.
            chunk_size:   Bytes per chunk (default 64 KB).

        Yields:
            Byte chunks.

        Raises:
            StorageReadError: If the file cannot be opened or read.
        """

    # ── Metadata ─────────────────────────────────────────────────────────────

    @abc.abstractmethod
    def get_file_metadata(self, storage_path: str) -> StorageMetadata:
        """
        Return metadata (size, existence) without reading the file content.

        Args:
            storage_path: Provider-relative path.

        Returns:
            :class:`StorageMetadata` with size and exists populated.
        """

    @abc.abstractmethod
    def exists(self, storage_path: str) -> bool:
        """
        Check whether a file exists at the given path.

        Args:
            storage_path: Provider-relative path.

        Returns:
            True if the file exists, False otherwise.
        """

    @abc.abstractmethod
    def generate_storage_path(
        self,
        user_id: int,
        document_id: str,
        extension: str,
    ) -> str:
        """
        Compute the provider-relative path for a document **without creating it**.

        Used for pre-computation and cleanup operations.

        Args:
            user_id:     Owner's user ID.
            document_id: Document UUID.
            extension:   Lowercase extension without dot.

        Returns:
            Provider-relative path string.
        """

    # ── Delete ───────────────────────────────────────────────────────────────

    @abc.abstractmethod
    def delete_file(self, storage_path: str) -> bool:
        """
        Remove a file from storage.

        Args:
            storage_path: Provider-relative path.

        Returns:
            True if the file was deleted, False if it did not exist.

        Raises:
            StorageDeleteError: If deletion fails for a reason other than
                the file not existing.
        """
