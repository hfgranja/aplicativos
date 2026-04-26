from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://pec:pec_secret@localhost:5432/pec_audit"
    REDIS_URL: str = "redis://localhost:6379/0"
    SECRET_KEY: str = "change-me-in-production-min-32-chars"
    ALGORITHM: str = "HS256"
    OTEL_SERVICE_NAME: str = "pec-audit"
    OTEL_EXPORTER_OTLP_ENDPOINT: str = ""
    OTEL_EXPORTER_ENABLED: str = "false"

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
