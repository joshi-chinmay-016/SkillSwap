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

    # ----------------------------
    # Embedding Engine (Day 69)
    # ----------------------------

    # Provider choice (e.g., gemini)
    EMBEDDING_PROVIDER: str = "gemini"

    # Default embedding model name
    EMBEDDING_MODEL: str = "gemini-embedding-001"

    # Optional specific API key override for embeddings (defaults to None / empty, falls back to GEMINI_API_KEY)
    EMBEDDING_API_KEY: str = ""

    # Configurable batch size for embedding generation
    EMBEDDING_BATCH_SIZE: int = 32

    # Maximum retry attempts for recoverable provider errors
    EMBEDDING_MAX_RETRIES: int = 3

    # Timeout in seconds for embedding API requests
    EMBEDDING_TIMEOUT: int = 30

    # Max concurrency limit for background tasks/batches
    EMBEDDING_CONCURRENCY: int = 5

    # Application-level embedding version
    EMBEDDING_VERSION: int = 1

    # Automatically retry FAILED embeddings after the main embedding job.
    # When True, a single retry pass fires after EMBEDDING_AUTO_RETRY_DELAY_SECONDS.
    EMBEDDING_AUTO_RETRY: bool = True

    # Seconds to wait before the automatic retry (gives rate-limits time to clear).
    EMBEDDING_AUTO_RETRY_DELAY_SECONDS: int = 30

    # ----------------------------
    # FAISS Vector Store (Day 70)
    # ----------------------------

    # Directory for FAISS index files (relative to working directory or absolute)
    # Must NOT be a developer-machine-specific path.
    FAISS_INDEX_DIR: str = "vector_store"

    # Filename for the FAISS binary index inside FAISS_INDEX_DIR
    FAISS_INDEX_FILENAME: str = "skillswap.index"

    # Filename for the JSON ID-mapping file alongside the FAISS index
    FAISS_MAPPING_FILENAME: str = "skillswap_mapping.json"

    # Expected embedding vector dimension.
    # Must match the output dimension of the configured EMBEDDING_MODEL.
    # gemini-embedding-001 (Gemini) produces 3072-dimensional vectors.
    FAISS_EMBEDDING_DIMENSION: int = 3072

    # Number of embeddings to process per indexing batch.
    # Bounds peak memory usage during large indexing runs.
    FAISS_INDEXING_BATCH_SIZE: int = 100

    # ----------------------------
    # Retrieval Engine (Day 71)
    # ----------------------------

    # Default number of results to return from a retrieval search.
    RETRIEVAL_DEFAULT_TOP_K: int = 5

    # Hard upper bound on top_k. Requests above this are rejected.
    RETRIEVAL_MAX_TOP_K: int = 20

    # Overfetch multiplier: FAISS candidate count = top_k * multiplier.
    # Extra candidates compensate for post-filtering (auth, lifecycle, dedup).
    # Example: top_k=5, multiplier=4 → fetch 20 candidates from FAISS.
    RETRIEVAL_CANDIDATE_MULTIPLIER: int = 4

    # Minimum inner-product score required to include a result.
    # IndexFlatIP with L2-normalised vectors: 0.0 = no threshold, 1.0 = exact match only.
    # Set to 0.0 to disable threshold filtering.
    RETRIEVAL_SIMILARITY_THRESHOLD: float = 0.0

    # Maximum allowed query string length in characters.
    RETRIEVAL_MAX_QUERY_LENGTH: int = 2000

    class Config:
        env_file = ".env"


settings = Settings()