"""
Ortam değişkenleri ve uygulama ayarları - BLUEPRINT core/config.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    PROJECT_NAME: str = "MemeVault"
    API_V1_STR: str = "/api/v1"

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://user:pass@localhost:5432/memevault"
    DATABASE_URL_SYNC: str = "postgresql+psycopg2://user:pass@localhost:5432/memevault"

    # JWT
    SECRET_KEY: str = "change-me-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 gün

    # Redis / Celery
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"

    # Object Storage (S3 uyumlu)
    S3_ENDPOINT_URL: str | None = None  # MinIO: http://localhost:9000
    S3_ACCESS_KEY: str = ""
    S3_SECRET_KEY: str = ""
    S3_BUCKET: str = "memevault"
    S3_REGION: str = "us-east-1"
    S3_USE_SSL: bool = True

    # AI (MVP)
    OPENAI_API_KEY: str = ""
    EMBEDDING_MODEL: str = "text-embedding-3-small"
    CAPTION_MODEL: str = "gpt-4o-mini"  # veya image captioning endpoint

    # Video Processing - Maliyet/Performans Ayarları
    KEYFRAME_COUNT: int = 3  # 1-5 arası, önerilen: 3 (maliyet/performans dengesi)
    ENABLE_TRANSCRIPTION: bool = True  # Whisper ile ses transkripti (ek ~$0.006/dk)
    
    # Ingestion
    YT_DLP_OUTPUT_TEMPLATE: str = "%(id)s.%(ext)s"
    DEFAULT_VIDEO_FORMAT: str = "mp4"


settings = Settings()
