from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://pec:pec_secret@localhost:5432/pec_identity"
    REDIS_URL: str = "redis://localhost:6379/0"
    SECRET_KEY: str = "change-me-in-production-min-32-chars"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    CORS_ORIGINS: str = ""
    ADMIN_EMAIL: str = "admin@pec.seduc.sp.gov.br"
    ADMIN_PASSWORD: str = "changeme123"
    OTEL_SERVICE_NAME: str = "pec-identity"
    OTEL_EXPORTER_OTLP_ENDPOINT: str = ""
    OTEL_EXPORTER_ENABLED: str = "false"

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
