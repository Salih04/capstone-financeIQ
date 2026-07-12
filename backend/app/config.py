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

    # CORS allowed origins (comma-separated). Default "*" keeps the public demo
    # working; set explicit origins in production. Credentials are auto-disabled
    # when "*" is used (see app/main.py).
    CORS_ALLOW_ORIGINS: str = "*"

    # Optional local research LLM support. If unavailable, the app falls back
    # to deterministic validated-report answers.
    research_llm_provider: str = "none"
    research_llm_base_url: str | None = None
    research_llm_model: str = "local-model"
    research_llm_timeout_seconds: float = 15.0
    research_score_llm_weight: float = 0.15

    # Optional Supabase Auth compatibility for frontend-managed sessions.
    # Legacy backend JWT auth remains supported for tests and old clients.
    # SUPABASE_JWT_SECRET → HS256 (legacy shared secret).
    # New Supabase "JWT Signing Keys" are asymmetric (RS256/ES256) and verified
    # via JWKS: set SUPABASE_URL (JWKS URL is derived) or SUPABASE_JWKS_URL.
    SUPABASE_JWT_SECRET: str | None = None
    SUPABASE_JWT_AUDIENCE: str = "authenticated"
    SUPABASE_AUTO_CREATE_USERS: bool = True
    SUPABASE_URL: str | None = None
    SUPABASE_JWKS_URL: str | None = None

    def supabase_jwks_url(self) -> str | None:
        if self.SUPABASE_JWKS_URL:
            return self.SUPABASE_JWKS_URL.strip()
        if self.SUPABASE_URL:
            return f"{self.SUPABASE_URL.rstrip('/')}/auth/v1/.well-known/jwks.json"
        return None

    def supabase_issuer(self) -> str | None:
        if self.SUPABASE_URL:
            return f"{self.SUPABASE_URL.rstrip('/')}/auth/v1"
        return None

    # ── Private/demo access control ──
    # Defaults preserve current behavior (open demo) so nothing breaks on deploy
    # or in local dev. Production locks down by setting PUBLIC_DEMO_MODE=false
    # (plus SUPABASE_JWT_SECRET so the backend can verify Supabase sessions).
    PUBLIC_DEMO_MODE: bool = True
    # When private (PUBLIC_DEMO_MODE=false) and this is true, the verified user's
    # email must be in APPROVED_EMAILS. Empty allowlist => deny all (fail closed).
    REQUIRE_APPROVED_USER: bool = False
    APPROVED_EMAILS: str = ""  # comma-separated, case-insensitive

    # Swagger /docs + /openapi.json. Disable in private production.
    ENABLE_PUBLIC_DOCS: bool = True

    # In-memory rate limiting for expensive endpoints (no external infra).
    RATE_LIMIT_ENABLED: bool = False
    RATE_LIMIT_REQUESTS_PER_MINUTE: int = 60

    def approved_emails_set(self) -> set[str]:
        return {e.strip().lower() for e in self.APPROVED_EMAILS.split(",") if e.strip()}

    class Config:
        env_file = ".env"
        # Local tooling may add provider-specific variables that this app does
        # not consume. Ignore those unknown entries while retaining validation
        # for every declared setting.
        extra = "ignore"


settings = Settings()
