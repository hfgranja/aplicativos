from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+psycopg2://pec_knowledge:pec@localhost/pec_knowledge"
    SECRET_KEY: str = "change-me-in-production"
    ENVIRONMENT: str = "development"
    SERVICE_NAME: str = "ms-011-knowledge"
    OTEL_EXPORTER_ENABLED: bool = False
    # JSON list of crawl sources — overrides built-in defaults when set
    SEDUC_CRAWLER_SOURCES: str = ""
    # Hour (0-23) and minute at which the daily crawl runs (America/Sao_Paulo)
    CRAWLER_HOUR: int = 6
    CRAWLER_MINUTE: int = 0

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
