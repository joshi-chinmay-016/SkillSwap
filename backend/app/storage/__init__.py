"""
Storage Package — Day 66 Part A2.

Public exports:
    StorageProvider          — abstract interface
    LocalStorageProvider     — filesystem implementation
    StorageService           — business-facing facade
    StorageProviderFactory   — provider selection from config
    StorageHealthService     — startup / health diagnostics
    StorageCleanupService    — orphan detection and consistency checks
"""
from app.storage.storage_provider import StorageProvider, StorageMetadata
from app.storage.local_storage_provider import LocalStorageProvider
from app.storage.storage_factory import StorageProviderFactory
from app.storage.storage_service import StorageService
from app.storage.storage_health_service import StorageHealthService
from app.storage.storage_cleanup_service import StorageCleanupService

__all__ = [
    "StorageProvider",
    "StorageMetadata",
    "LocalStorageProvider",
    "StorageProviderFactory",
    "StorageService",
    "StorageHealthService",
    "StorageCleanupService",
]
