from pydantic_settings import BaseSettings, SettingsConfigDict

"""
config.py — Centralised settings loaded from environment variables / .env file 

Usage anywhere in the codebase:
    from app.config import settings
    print(settings.DATABASE_URL)
"""

# TODO in phase1, create custom llm for all llm providers to use in the future, and move _get_llm_with_tools() to this file as well, so that we can reuse it across the codebase without importing node.py
# TODO in phase 3 add google gemini support api key
class Settings(BaseSettings):
    # ── LLM ──────────────────────────────────────────────────────────────────
    MODEL_PROVIDER: str = "openai"          # openai | anthropic | ollama  | custom
    OPENAI_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""
    OLLAMA_BASE_URL: str = "http://localhost:11434"     # Llama 3 | Mistral | DeepSeek | Gemma | Qwen , for self hosted models 
    LLM_MODEL: str = "gpt-4o"

    # ── Database ─────────────────────────────────────────────────────────────
    DATABASE_URL: str = "postgresql://agent_user:agent_pass@localhost:5432/agent_db"

    # ── Security ──────────────────────────────────────────────────────────────
    # TODO in phase 2, it load from .env with more securety settings 
    SECRET_KEY: str = "change-me"  # JWT token signing | password reset tokens |session security
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # ── App ───────────────────────────────────────────────────────────────────
    APP_ENV: str = "development"
    LOG_LEVEL: str = "INFO"        # DEBUG | INFO | WARNING | ERROR | CRITICAL for debugging and monitoring
    BACKEND_URL: str = "http://localhost:8000"

    model_config = SettingsConfigDict(      # Pydantic v2 style config Pydantic automatically use internally predefined setting features
        env_file=".env",
        env_file_encoding="utf-8",     # Read the .env file using UTF-8 text encoding
        extra="ignore",
    )


# Single shared instance — import this everywhere
settings = Settings()
