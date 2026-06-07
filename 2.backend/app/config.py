import secrets

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/capstone_db"

    # No hardcoded secret in source. If SECRET_KEY is not provided via env/.env
    # a random one is generated per process (JWTs reset on restart). Production
    # MUST set SECRET_KEY explicitly.
    SECRET_KEY: str = Field(default_factory=lambda: secrets.token_urlsafe(48))
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours

    # Optional local research LLM support. If unavailable, the app falls back
    # to deterministic validated-report answers.
    research_llm_provider: str = "none"
    research_llm_base_url: str | None = None
    research_llm_model: str = "local-model"
    research_llm_timeout_seconds: float = 15.0
    research_score_llm_weight: float = 0.15

    class Config:
        env_file = ".env"


settings = Settings()
