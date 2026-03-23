from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # App
    APP_NAME: str = "AuditAI Test Platform"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # Database
    DATABASE_URL: str = "sqlite:///./auditai.db"

    # Redis / Celery
    REDIS_URL: str = "redis://localhost:6379/0"

    # Auth
    SECRET_KEY: str = "dev-secret-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Admin seed
    ADMIN_EMAIL: str = "admin@auditai.local"
    ADMIN_PASSWORD: str = "changeme123"

    # LLM
    OLLAMA_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3.2"
    ANTHROPIC_API_KEY: Optional[str] = None

    # Storage
    ARTIFACT_STORE_PATH: str = "./artifacts"

    # CORS
    CORS_ORIGINS: list[str] = [
        "http://localhost:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5173",
    ]

    # PR Automation (Enhancement 3)
    GITHUB_TOKEN: str = ""
    GITLAB_TOKEN: str = ""
    GITLAB_URL: str = "https://gitlab.com"

    # OpenTelemetry (Enhancement 4)
    # Set to OTLP endpoint (e.g. http://jaeger:4317) to enable distributed tracing
    OTEL_EXPORTER_OTLP_ENDPOINT: str = ""
    OTEL_SERVICE_NAME: str = "auditai-backend"

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
