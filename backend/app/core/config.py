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

    class Config:
        env_file = ".env"


settings = Settings()