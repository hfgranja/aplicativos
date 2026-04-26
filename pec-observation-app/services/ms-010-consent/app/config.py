from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://pec:pec_secret@localhost:5432/pec_consent"
    REDIS_URL: str = "redis://localhost:6379/0"
    SECRET_KEY: str = "change-me-in-production-min-32-chars"
    ALGORITHM: str = "HS256"
    MINIO_ENDPOINT: str = "http://minio:9000"
    MINIO_ROOT_USER: str = "minioadmin"
    MINIO_ROOT_PASSWORD: str = "minioadmin"
    MINIO_BUCKET_AUDIO: str = "audio-uploads"
    AUDIO_RETENTION_DAYS: int = 7
    OTEL_SERVICE_NAME: str = "pec-consent"
    OTEL_EXPORTER_OTLP_ENDPOINT: str = ""
    OTEL_EXPORTER_ENABLED: str = "false"

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
