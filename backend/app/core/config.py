from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    environment: str = "development"

    # Meta / Graph API
    fb_app_id: str = ""
    fb_app_secret: str = ""
    fb_access_token: str = ""
    graph_api_version: str = "v25.0"

    # YouTube Data API v3
    youtube_api_key: str = ""

    # Whisper (transcripción de audio/video)
    whisper_model: str = "small"  # tiny | base | small | medium
    whisper_compute: str = "int8"  # int8 es eficiente en CPU
    whisper_cache_dir: str = "/root/.cache/whisper"

    # Postgres
    database_url: str = "postgresql+asyncpg://osint:osint@postgres:5432/osint_monitor"

    # Redis
    redis_url: str = "redis://redis:6379/0"

    # MinIO
    minio_endpoint: str = "minio:9000"
    minio_root_user: str = "osint_admin"
    minio_root_password: str = "osint_admin_password"
    minio_bucket: str = "osint-media"
    minio_secure: bool = False

    # Ollama
    ollama_host: str = "http://ollama:11434"
    ollama_llm_model: str = "qwen2.5"
    ollama_embed_model: str = "nomic-embed-text"

    # Telegram
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""

    # Scheduler
    poll_default_interval: int = 300

    # CORS
    backend_cors_origins: list[str] = ["http://localhost:3000"]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
