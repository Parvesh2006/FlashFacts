from pathlib import Path
from typing import List, Union
from urllib.parse import urlsplit
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator, model_validator

INSECURE_DEFAULT_SECRETS = {
    "flashfacts_secure_exam_portal_key_2026",
    "secret",
    "changeme",
    "password",
    "test",
    "replace-with-a-strong-random-secret-before-deployment",
}

DEV_DEFAULT_SECRET = "flashfacts_dev_insecure_jwt_secret_key_32bytes_min"
DEV_DEFAULT_CORS = [
    "http://localhost:3000",
    "http://localhost:8000",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:8000",
]


def validate_cors_origin(origin: str) -> str:
    """Validate that a CORS origin is a well-formed, absolute HTTP or HTTPS origin."""
    if not isinstance(origin, str):
        raise ValueError(f"Production configuration error: CORS origin must be a string, got {type(origin).__name__}")
    origin = origin.strip()
    if not origin:
        raise ValueError("Production configuration error: Empty or whitespace-only CORS origin is not permitted.")
    if origin == "*":
        raise ValueError(
            "Production configuration error: Wildcard CORS origin ('*') is rejected in production "
            "when credentials are enabled. Configure explicit trusted origin domains."
        )
    parsed = urlsplit(origin)
    if parsed.scheme not in ("http", "https"):
        raise ValueError(
            f"Production configuration error: Invalid CORS origin '{origin}'. "
            "Origin must start with an absolute 'http://' or 'https://' scheme."
        )
    if not parsed.netloc or not parsed.hostname:
        raise ValueError(
            f"Production configuration error: Invalid CORS origin '{origin}'. Missing valid hostname."
        )
    if parsed.username or parsed.password:
        raise ValueError(
            f"Production configuration error: Invalid CORS origin '{origin}'. "
            "User credentials in origin are not permitted."
        )
    if parsed.path:
        raise ValueError(
            f"Production configuration error: Invalid CORS origin '{origin}'. "
            f"CORS origins must not include a path component ('{parsed.path}')."
        )
    if parsed.query:
        raise ValueError(
            f"Production configuration error: Invalid CORS origin '{origin}'. "
            "CORS origins must not include query parameters."
        )
    if parsed.fragment:
        raise ValueError(
            f"Production configuration error: Invalid CORS origin '{origin}'. "
            "CORS origins must not include a fragment identifier."
        )
    return origin


class Settings(BaseSettings):
    PROJECT_NAME: str = "FlashFacts API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    APP_ENV: str = "development"
    SECRET_KEY: str = "flashfacts_secure_exam_portal_key_2026"

    # OAuth / Dual Authentication
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""

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
    AI_BASE_URL: str = ""
    AI_MODEL: str = "gpt-4o-mini"
    AI_MAX_INPUT_CHARS: int = 6000
    OPENAI_API_KEY: str = ""
    GEMINI_API_KEY: str = ""

    # Ollama Integration
    OLLAMA_BASE_URL: str = "http://host.docker.internal:11434"
    OLLAMA_TIMEOUT: int = 150

    # Ingestion
    INGESTION_ENABLED: bool = False
    INGESTION_INTERVAL_MINUTES: int = 30
    INGESTION_REQUEST_TIMEOUT: float = 15.0
    INGESTION_MAX_RETRIES: int = 3
    INGESTION_RETRY_BACKOFF: float = 1.0
    INGESTION_USER_AGENT: str = "FlashFacts/0.1 (+https://example.com)"
    INGESTION_FRESHNESS_HOURS: int = 168

    # CORS
    CORS_ORIGINS: Union[str, List[str]] = ["*"]

    @field_validator("CORS_ORIGINS", mode="before")
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            v_trimmed = v.strip()
            if not v_trimmed:
                return []
            if v_trimmed.startswith("[") and v_trimmed.endswith("]"):
                import json
                try:
                    parsed = json.loads(v_trimmed)
                    if isinstance(parsed, list):
                        return [str(i).strip() for i in parsed]
                except Exception:
                    return [v_trimmed]
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, list):
            return [str(i).strip() for i in v]
        return v

    @model_validator(mode="after")
    def validate_production_security(self) -> "Settings":
        env = (self.APP_ENV or "development").strip().lower()
        is_production = env in ("production", "prod", "staging")

        # 1. JWT Secret Validation
        secret = (self.SECRET_KEY or "").strip()
        if is_production:
            if not secret:
                raise ValueError(
                    "Production configuration error: SECRET_KEY is missing. "
                    "A strong, unique cryptographic secret of at least 32 characters must be provided in production."
                )
            if secret in INSECURE_DEFAULT_SECRETS or len(secret) < 32:
                raise ValueError(
                    "Production configuration error: Insecure or default SECRET_KEY detected. "
                    "Production requires a custom, non-default secret of at least 32 characters."
                )
        else:
            if not secret:
                self.SECRET_KEY = DEV_DEFAULT_SECRET

        # 2. CORS Origins Validation
        origins = self.CORS_ORIGINS
        if isinstance(origins, list):
            if is_production:
                if not origins:
                    raise ValueError(
                        "Production configuration error: CORS_ORIGINS cannot be empty in production. "
                        "Specify trusted client origins."
                    )
                for origin in origins:
                    validate_cors_origin(origin)
            else:
                if not origins or any(o == "*" or not o for o in origins):
                    self.CORS_ORIGINS = list(DEV_DEFAULT_CORS)

        return self

    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parents[4] / ".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()
