from typing import List, Union
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator


class Settings(BaseSettings):
    PROJECT_NAME: str = "FlashFacts API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    APP_ENV: str = "development"

    # Database
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/flashfacts"

    # Cache / Message Queue
    REDIS_URL: str = "redis://localhost:6379/0"

    # LLM (Phase 2)
    # Backwards-compatible key from Phase 2
    LLM_API_KEY: str = ""

    # AI Provider (Phase 3A)
    AI_PROVIDER: str = "fallback"
    AI_API_KEY: str = ""
    AI_MODEL: str = "gpt-4o-mini"

    # Ingestion
    INGESTION_ENABLED: bool = False
    INGESTION_INTERVAL_MINUTES: int = 30
    INGESTION_REQUEST_TIMEOUT: float = 15.0
    INGESTION_MAX_RETRIES: int = 3
    INGESTION_RETRY_BACKOFF: float = 1.0
    INGESTION_USER_AGENT: str = "FlashFacts/0.1 (+https://example.com)"

    # CORS
    CORS_ORIGINS: Union[str, List[str]] = ["*"]

    @field_validator("CORS_ORIGINS", mode="before")
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            if not v:
                return []
            if v.startswith("[") and v.endswith("]"):
                import json
                return json.loads(v)
            return [i.strip() for i in v.split(",")]
        return v

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()
