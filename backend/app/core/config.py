from pydantic_settings import BaseSettings


class Settings(BaseSettings):

    DATABASE_URL: str

    SECRET_KEY: str

    ALGORITHM: str = "HS256"

    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # ----------------------------
    # AI
    # ----------------------------

    GEMINI_API_KEY: str

    GEMINI_MODEL: str = "gemini-1.5-flash"

    MENTOR_MAX_HISTORY_MESSAGES: int = 10

    MENTOR_TOOL_TIMEOUT_SECONDS: int = 5

    MENTOR_INTENT_CONFIDENCE_THRESHOLD: float = 0.50

    MENTOR_LLM_FALLBACK_ENABLED: bool = False

    # ----------------------------
    # Long-Term Memory (Day 65)
    # ----------------------------

    # Master switch — disable to skip extraction entirely
    MEMORY_EXTRACTION_ENABLED: bool = True

    # Default importance when not specified
    MEMORY_DEFAULT_IMPORTANCE: str = "MEDIUM"

    # Max memories injected into a single mentor prompt
    MEMORY_MAX_RETRIEVED: int = 5

    # Number of days of inactivity before a memory becomes an archive candidate
    MEMORY_DECAY_DAYS: int = 365

    # Similarity threshold for duplicate title detection (0–100, Levenshtein-style)
    MEMORY_DUPLICATE_THRESHOLD: int = 90

    # Ranking weights — must sum to 1.0 (enforced at startup by service)
    MEMORY_WEIGHT_IMPORTANCE: float = 0.35
    MEMORY_WEIGHT_CATEGORY: float = 0.25
    MEMORY_WEIGHT_KEYWORD: float = 0.25
    MEMORY_WEIGHT_RECENCY: float = 0.15

    # Extra priority added for pinned memories (added to raw score)
    MEMORY_PINNED_PRIORITY_BONUS: float = 0.5

    # ----------------------------
    # Document Storage (Day 66)
    # ----------------------------

    # Storage backend: LOCAL | S3 | AZURE | GCS | MINIO
    STORAGE_PROVIDER: str = "LOCAL"

    # Root directory for uploaded files (LocalStorageProvider)
    UPLOAD_DIRECTORY: str = "uploads"

    # Maximum upload size in bytes (default: 25 MB)
    MAX_FILE_SIZE: int = 26_214_400

    # Duplicate upload policy: REJECT | REUSE | ALLOW
    # REJECT: same user, same file → 409 Conflict
    # REUSE: return existing metadata without re-storing
    # ALLOW: store independently (creates multiple records)
    DUPLICATE_UPLOAD_POLICY: str = "REJECT"

    # Temporary directory for in-progress uploads (future use)
    TEMP_DIRECTORY: str = "uploads/tmp"

    # ----------------------------
    # Chunking Engine (Day 68)
    # ----------------------------

    # Default maximum character count per chunk
    CHUNK_SIZE: int = 800

    # Default character overlap between adjacent chunks (context preservation)
    CHUNK_OVERLAP: int = 150

    # Default strategy name — must match a registered ChunkStrategy.name
    CHUNK_STRATEGY: str = "recursive"

    # Semantic version of the default strategy (stored with every chunk)
    CHUNK_STRATEGY_VERSION: str = "1.0.0"

    # Approximate maximum tokens per chunk (used for future embedding model gating)
    CHUNK_MAX_TOKENS: int = 1024

    class Config:
        env_file = ".env"


settings = Settings()