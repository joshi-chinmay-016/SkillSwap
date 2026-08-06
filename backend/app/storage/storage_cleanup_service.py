"""
StorageCleanupService — orphan detection and consistency checks (Day 66 Part A2).

Responsibilities:
    - Find files on disk that have no corresponding database record (orphans).
    - Find database records that have no corresponding file on disk (dangling metadata).
    - Validate that stored file sizes match the database.
    - Provide a dry-run mode (default) so no destructive operations happen automatically.

IMPORTANT:
    This service does NOT automatically delete user documents.
    All cleanup actions require explicit administrator invocation.
    Future: connect to a scheduled job or admin endpoint.

Usage:
    from app.storage.storage_cleanup_service import StorageCleanupService
    from app.storage.storage_service import storage_service

    cleanup = StorageCleanupService(storage_service)
    report = cleanup.scan(db)
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Optional

from app.storage.storage_provider import StorageProvider
from app.storage.storage_service import StorageService

logger = logging.getLogger(__name__)


@dataclass
class CleanupReport:
    """Result of a cleanup scan."""

    orphaned_files: list[str] = field(default_factory=list)
    """Files present on disk but missing from the database."""

    dangling_records: list[str] = field(default_factory=list)
    """Database document IDs whose physical file is missing."""

    size_mismatches: list[dict] = field(default_factory=list)
    """Records where actual file size differs from stored metadata."""

    total_files_on_disk: int = 0
    total_records_in_db: int = 0
    errors: list[str] = field(default_factory=list)

    @property
    def healthy(self) -> bool:
        return (
            len(self.orphaned_files) == 0
            and len(self.dangling_records) == 0
            and len(self.size_mismatches) == 0
        )


class StorageCleanupService:
    """
    Scans for inconsistencies between the filesystem and database metadata.

    Args:
        storage_service: The :class:`StorageService` instance to use.
    """

    def __init__(self, storage_service: StorageService) -> None:
        self._storage = storage_service

    def scan(self, db) -> CleanupReport:
        """
        Scan for orphaned files and dangling database records.

        Args:
            db: SQLAlchemy ``Session``.

        Returns:
            :class:`CleanupReport` describing all detected issues.
        """
        report = CleanupReport()

        try:
            # ── Step 1: collect all files currently on disk ────────────────
            disk_paths = self._get_disk_files()
            disk_path_set = set(disk_paths)
            report.total_files_on_disk = len(disk_paths)

            # ── Step 2: collect all active records from the database ───────
            db_records = self._get_db_records(db)
            db_path_map: dict[str, object] = {
                r.storage_path: r for r in db_records
            }
            report.total_records_in_db = len(db_records)

            # ── Step 3: orphaned files (disk but not in DB) ────────────────
            for path in disk_paths:
                if path not in db_path_map:
                    report.orphaned_files.append(path)
                    logger.warning("Orphaned file detected: %s", path)

            # ── Step 4: dangling records (DB but not on disk) ──────────────
            for storage_path, record in db_path_map.items():
                if storage_path not in disk_path_set:
                    report.dangling_records.append(str(record.id))
                    logger.warning(
                        "Dangling record detected: document_id=%s storage_path=%s",
                        record.id,
                        storage_path,
                    )

            # ── Step 5: size mismatch checks ───────────────────────────────
            for storage_path, record in db_path_map.items():
                if storage_path in disk_path_set:
                    meta = self._storage.get_file_metadata(storage_path)
                    if meta.size != record.file_size:
                        mismatch = {
                            "document_id": str(record.id),
                            "storage_path": storage_path,
                            "expected_size": record.file_size,
                            "actual_size": meta.size,
                        }
                        report.size_mismatches.append(mismatch)
                        logger.warning("Size mismatch: %s", mismatch)

        except Exception as exc:  # noqa: BLE001
            report.errors.append(str(exc))
            logger.error("Cleanup scan error: %s", exc)

        if report.healthy:
            logger.info("StorageCleanupService scan complete — storage is consistent.")
        else:
            logger.warning(
                "StorageCleanupService scan found issues — orphans=%d dangling=%d mismatches=%d",
                len(report.orphaned_files),
                len(report.dangling_records),
                len(report.size_mismatches),
            )

        return report

    def delete_orphan(self, storage_path: str, dry_run: bool = True) -> bool:
        """
        Delete a single orphaned file.

        Args:
            storage_path: Provider-relative path of the orphan.
            dry_run:      If True (default), log the action but do not delete.

        Returns:
            True if the file was deleted (or would be in dry_run mode).
        """
        if dry_run:
            logger.info("DRY-RUN: would delete orphan — %s", storage_path)
            return True

        deleted = self._storage.delete_file(storage_path)
        if deleted:
            logger.info("Orphan deleted — %s", storage_path)
        return deleted

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _get_disk_files(self) -> list[str]:
        """Return all provider-relative paths currently on disk."""
        provider = self._storage.provider
        if hasattr(provider, "list_all_files"):
            return provider.list_all_files()
        logger.debug("Provider does not support list_all_files — skipping disk scan.")
        return []

    def _get_db_records(self, db) -> list:
        """Return all non-archived Document records from the database."""
        try:
            from app.models.document import Document, DocumentStatus

            return (
                db.query(Document)
                .filter(Document.status != DocumentStatus.ARCHIVED.value)
                .filter(Document.deleted_at.is_(None))
                .all()
            )
        except Exception as exc:  # noqa: BLE001
            logger.error("Failed to query documents for cleanup scan: %s", exc)
            return []
