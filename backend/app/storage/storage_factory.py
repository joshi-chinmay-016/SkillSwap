"""
StorageProviderFactory — selects the configured storage backend (Day 66 Part A2).

Currently supported providers:
    LOCAL   → LocalStorageProvider

Future providers (not implemented — add when needed):
    S3      → S3StorageProvider
    AZURE   → AzureBlobStorageProvider
    GCS     → GCSStorageProvider
    MINIO   → MinIOStorageProvider

Changing the provider requires only:
    1. Set STORAGE_PROVIDER=S3 in .env.
    2. Implement S3StorageProvider satisfying the StorageProvider interface.
    3. Register the mapping in PROVIDER_MAP below.

No changes needed in DocumentService, DocumentRouter, or any parsing code.
"""
import logging

from app.core.config import settings
from app.exceptions.storage_exceptions import StorageValidationError
from app.storage.storage_provider import StorageProvider

logger = logging.getLogger(__name__)

# ── Provider registry ─────────────────────────────────────────────────────────
# Add new providers here as they are implemented.
# Key: uppercase provider name from config.
# Value: factory callable that returns a StorageProvider instance.
_PROVIDER_MAP: dict[str, object] = {}  # populated lazily below


def _build_provider_map() -> dict[str, object]:
    """
    Build the provider registry lazily to avoid importing cloud SDKs
    (boto3, azure-storage-blob, etc.) unless they are actually used.
    """
    from app.storage.local_storage_provider import LocalStorageProvider

    return {
        "LOCAL": lambda: LocalStorageProvider(
            base_directory=settings.UPLOAD_DIRECTORY
        ),
    }


class StorageProviderFactory:
    """
    Factory that creates and returns the configured :class:`StorageProvider`.

    Usage (in dependency injection or service initialisation):

        provider = StorageProviderFactory.get_provider()

    The provider name is read from ``settings.STORAGE_PROVIDER`` (uppercased).
    """

    @staticmethod
    def get_provider(provider_name: str | None = None) -> StorageProvider:
        """
        Return a fully-initialised :class:`StorageProvider`.

        Args:
            provider_name: Override the configured provider for testing.
                           Defaults to ``settings.STORAGE_PROVIDER``.

        Returns:
            Concrete :class:`StorageProvider` instance.

        Raises:
            StorageValidationError: If the requested provider is not registered.
        """
        provider_map = _build_provider_map()
        name = (provider_name or settings.STORAGE_PROVIDER).upper()

        factory = provider_map.get(name)
        if factory is None:
            supported = ", ".join(sorted(provider_map.keys()))
            logger.error(
                "Unknown storage provider '%s'. Supported: %s", name, supported
            )
            raise StorageValidationError(
                f"Unknown storage provider '{name}'. Supported providers: {supported}."
            )

        provider = factory()
        logger.info("StorageProviderFactory → %s (%s)", name, type(provider).__name__)
        return provider
