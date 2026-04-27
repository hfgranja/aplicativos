from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    SERVICE_NAME:  str = "pec-best-practices"
    DATABASE_URL:  str = "postgresql://pec:pec_secret@localhost:5432/pec_best_practices"
    REDIS_URL:     str = "redis://localhost:6379"
    SECRET_KEY:    str = "change-me"
    MINIO_ENDPOINT:    str = "http://minio:9000"
    MINIO_ACCESS_KEY:  str = "minioadmin"
    MINIO_SECRET_KEY:  str = "minioadmin"
    AUDIO_SERVICE_URL:        str = "http://ms-004-audio-ingestion:8004"
    TRANSCRIPTION_SERVICE_URL: str = "http://ms-005-transcription:8005"
    OTEL_EXPORTER_ENABLED: bool = False

    class Config:
        env_file = ".env"


settings = Settings()
