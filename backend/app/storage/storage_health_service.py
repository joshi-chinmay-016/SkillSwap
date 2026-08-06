"""
StorageHealthService — startup and runtime diagnostics (Day 66 Part A2).

Responsibilities:
    - Verify the upload directory exists.
    - Verify the directory is readable.
    - Verify the directory is writable.
    - Report available disk space (optional — best-effort).
    - Expose a structured health report suitable for a /health endpoint.

Usage:
    from app.storage.storage_health_service import StorageHealthService
    from app.storage.storage_service import storage_service

    health = StorageHealthService(storage_service.provider)
    report = health.check()
    # report.healthy → bool
"""
from __future__ import annotations

import logging
import os
import shutil
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from app.storage.storage_provider import StorageProvider

logger = logging.getLogger(__name__)


@dataclass
class StorageHealthReport:
    """Structured result of a health check."""

    healthy: bool
    provider: str
    directory_exists: bool
    directory_readable: bool
    directory_writable: bool
    disk_total_bytes: Optional[int] = None
    disk_used_bytes: Optional[int] = None
    disk_free_bytes: Optional[int] = None
    errors: list[str] = field(default_factory=list)

    @property
    def disk_usage_percent(self) -> Optional[float]:
        if self.disk_total_bytes and self.disk_total_bytes > 0:
            return round(self.disk_used_bytes / self.disk_total_bytes * 100, 2)
        return None


class StorageHealthService:
    """
    Performs health diagnostics against a :class:`StorageProvider`.

    Currently works with :class:`LocalStorageProvider`.
    Future providers should extend this class or supply their own
    health-check implementation.
    """

    def __init__(self, provider: StorageProvider) -> None:
        self._provider = provider

    def check(self) -> StorageHealthReport:
        """
        Run all health checks and return a consolidated :class:`StorageHealthReport`.

        Never raises — all errors are captured in the report.
        """
        provider_name = type(self._provider).__name__
        errors: list[str] = []

        directory_exists = False
        directory_readable = False
        directory_writable = False
        disk_info: dict = {}

        # ── Check 1: directory exists ──────────────────────────────────────
        base_dir = self._get_base_directory()
        if base_dir:
            directory_exists = base_dir.exists()
            if not directory_exists:
                errors.append(f"Upload directory does not exist: {base_dir}")
            else:
                # ── Check 2: readable ──────────────────────────────────────
                directory_readable = os.access(base_dir, os.R_OK)
                if not directory_readable:
                    errors.append(f"Upload directory is not readable: {base_dir}")

                # ── Check 3: writable ──────────────────────────────────────
                directory_writable = self._probe_write(base_dir, errors)

                # ── Check 4: disk space (best-effort) ─────────────────────
                try:
                    usage = shutil.disk_usage(base_dir)
                    disk_info = {
                        "disk_total_bytes": usage.total,
                        "disk_used_bytes": usage.used,
                        "disk_free_bytes": usage.free,
                    }
                except Exception as exc:  # noqa: BLE001
                    logger.debug("Disk usage check skipped: %s", exc)
        else:
            errors.append("Cannot determine base directory for provider.")

        healthy = directory_exists and directory_readable and directory_writable and not errors

        report = StorageHealthReport(
            healthy=healthy,
            provider=provider_name,
            directory_exists=directory_exists,
            directory_readable=directory_readable,
            directory_writable=directory_writable,
            errors=errors,
            **disk_info,
        )

        if healthy:
            logger.info("StorageHealthService check passed — provider=%s", provider_name)
        else:
            logger.warning(
                "StorageHealthService check FAILED — provider=%s errors=%s",
                provider_name,
                errors,
            )

        return report

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _get_base_directory(self) -> Optional[Path]:
        """
        Extract base directory from the provider if it exposes one.
        Falls back to None for providers that do not have a local directory.
        """
        base_dir = getattr(self._provider, "base_directory", None)
        if base_dir is not None:
            return Path(base_dir)
        return None

    def _probe_write(self, directory: Path, errors: list[str]) -> bool:
        """
        Attempt to create and delete a temp file in ``directory``.

        Returns True if successful, False otherwise (and appends to ``errors``).
        """
        try:
            with tempfile.NamedTemporaryFile(dir=directory, delete=True) as tmp:
                tmp.write(b"health_check")
            return True
        except Exception as exc:  # noqa: BLE001
            errors.append(f"Upload directory is not writable: {directory} — {exc}")
            return False
