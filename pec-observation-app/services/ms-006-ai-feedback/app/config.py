from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://pec:pec_secret@localhost:5432/pec_ai_feedback"
    REDIS_URL: str = "redis://localhost:6379/0"
    SECRET_KEY: str = "change-me-in-production-min-32-chars"
    ALGORITHM: str = "HS256"
    OLLAMA_BASE_URL: str = "http://ollama:11434"
    OLLAMA_MODEL: str = "llama3.2"
    ANTHROPIC_API_KEY: str = ""
    LLM_PROVIDER: str = "ollama"  # ollama | anthropic
    KNOWLEDGE_BASE_URL: str = "http://ms-011-knowledge:8011"
    KNOWLEDGE_MAX_CHUNKS: int = 5
    LEARNING_SERVICE_URL: str = "http://ms-013-learning:8000"
    OTEL_SERVICE_NAME: str = "pec-ai-feedback"
    OTEL_EXPORTER_OTLP_ENDPOINT: str = ""
    OTEL_EXPORTER_ENABLED: str = "false"

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
