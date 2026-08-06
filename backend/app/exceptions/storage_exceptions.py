"""
Storage Exceptions — Day 66 Part A2.

Custom exception hierarchy for the Storage Abstraction Layer.
Never expose raw filesystem or cloud-SDK exceptions outside this layer.

Exception tree:
    StorageError (base)
    ├── StorageUnavailable    — provider unreachable / directory missing
    ├── StorageWriteError     — failed to persist a file
    ├── StorageReadError      — failed to read / stream a file
    ├── StorageDeleteError    — failed to delete a file
    └── StorageValidationError — bad input: path traversal, unknown provider, etc.
"""


class StorageError(Exception):
    """Base class for all storage-layer exceptions."""

    def __init__(self, message: str, *, cause: Exception | None = None) -> None:
        super().__init__(message)
        self.cause = cause
        self.message = message

    def __str__(self) -> str:
        if self.cause:
            return f"{self.message} (caused by: {self.cause})"
        return self.message


class StorageUnavailable(StorageError):
    """
    Raised when the storage provider or backing directory is unreachable.

    Examples:
        - Upload directory does not exist and cannot be created.
        - Cloud provider endpoint is down (future).
    """


class StorageWriteError(StorageError):
    """
    Raised when a file cannot be written to storage.

    Examples:
        - Disk full.
        - Permission denied on the upload directory.
        - IO error during multipart save.
    """


class StorageReadError(StorageError):
    """
    Raised when a stored file cannot be read or streamed.

    Examples:
        - File missing from disk (metadata / physical mismatch).
        - Permission denied on the file.
        - IO error during streaming.
    """


class StorageDeleteError(StorageError):
    """
    Raised when a stored file cannot be deleted.

    Examples:
        - File already removed by an external process.
        - Permission denied.
    """


class StorageValidationError(StorageError):
    """
    Raised when storage input fails validation before any IO occurs.

    Examples:
        - Path traversal detected (``../../etc/passwd``).
        - Unsupported storage provider name in configuration.
        - Symbolic link detected at upload path.
    """
