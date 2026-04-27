from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+psycopg2://pec_knowledge:pec@localhost/pec_knowledge"
    SECRET_KEY: str = "change-me-in-production"
    ENVIRONMENT: str = "development"
    SERVICE_NAME: str = "ms-011-knowledge"
    OTEL_EXPORTER_ENABLED: bool = False

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
