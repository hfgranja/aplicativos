from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql://pec:pec_secret@postgres:5432/pec_learning"
    redis_url: str = "redis://redis:6379/0"
    ollama_base_url: str = "http://ollama:11434"
    ollama_model: str = "llama3.2"
    ollama_embedding_model: str = "nomic-embed-text"
    # How many approved feedback examples to include in Modelfile few-shots
    modelfile_max_examples: int = 20
    # Rebuild model when this many new approved examples accumulate
    rebuild_threshold: int = 5
    # Name for the fine-tuned Ollama model
    pec_model_name: str = "pec-pedagogo"
    # External service URLs
    knowledge_service_url: str = "http://ms-011-knowledge:8011"
    service_name: str = "pec-learning"
    environment: str = "development"
    otel_exporter_enabled: bool = False

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
