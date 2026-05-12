"""
config.py — Centralised settings loaded from environment / .env file.

Usage anywhere in the codebase:
    from app.config import settings
    print(settings.DATABASE_URL)
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # ── LLM ──────────────────────────────────────────────────────────────────
    MODEL_PROVIDER: str = "openai"          # openai | anthropic | ollama
    OPENAI_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    LLM_MODEL: str = "gpt-4o"

    # ── Database ─────────────────────────────────────────────────────────────
    DATABASE_URL: str = "postgresql://agent_user:agent_pass@localhost:5432/agent_db"

    # ── Security ──────────────────────────────────────────────────────────────
    SECRET_KEY: str = "change-me"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # ── App ───────────────────────────────────────────────────────────────────
    APP_ENV: str = "development"
    LOG_LEVEL: str = "INFO"
    BACKEND_URL: str = "http://localhost:8000"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


# Single shared instance — import this everywhere
settings = Settings()
