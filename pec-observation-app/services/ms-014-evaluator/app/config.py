from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql://pec:pec_secret@postgres:5432/pec_evaluator"
    redis_url: str = "redis://redis:6379/0"
    ollama_base_url: str = "http://ollama:11434"
    ollama_model: str = "llama3.2"
    ollama_embedding_model: str = "nomic-embed-text"
    learning_service_url: str = "http://ms-013-learning:8000"
    # Quality threshold below which model is considered degraded
    quality_alert_threshold: float = 0.60
    # Rolling window for health computation (number of recent evaluations)
    health_window: int = 20
    # Minimum quality score to include example in Modelfile
    min_example_quality: float = 0.45
    # Max synthetic examples to generate per rebuild cycle
    max_synthetic_per_cycle: int = 5
    # Recency half-life in days for weight decay
    recency_half_life_days: float = 90.0
    service_name: str = "pec-evaluator"
    environment: str = "development"
    otel_exporter_enabled: bool = False

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
