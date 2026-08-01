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

    class Config:
        env_file = ".env"


settings = Settings()