from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="STEMSAI_", extra="ignore")

    app_name: str = "STEMS AI"
    environment: str = "development"
    debug: bool = True

    # Armazenamento
    storage_root: str = "./storage"
    uploads_dir: str = "uploads"
    results_dir: str = "results"

    # Limites
    max_upload_size_mb: float = 200.0
    allowed_extensions: tuple[str, ...] = (".mp3", ".wav", ".flac", ".aiff", ".aac", ".ogg", ".m4a")

    # Redis / fila
    redis_url: str = "redis://localhost:6379/0"
    queue_name: str = "stemsai:separation"

    # Separação
    default_engine: str = "htdemucs_6s"
    device: str = "cuda"  # cai para "cpu" automaticamente se cuda indisponível
    demucs_model_cache_dir: str = "./models_cache/demucs"
    mdx_model_cache_dir: str = "./models_cache/mdx"

    # CORS
    cors_allow_origins: tuple[str, ...] = ("http://localhost:3000",)

    # WebSocket
    ws_heartbeat_seconds: int = 15


@lru_cache
def get_settings() -> Settings:
    return Settings()
