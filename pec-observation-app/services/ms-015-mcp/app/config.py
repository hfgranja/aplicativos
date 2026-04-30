from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # DATABASE_URL = primary (pec_learning) — consistent with other services
    database_url:           str = "postgresql://pec:pec_secret@postgres:5432/pec_learning"
    database_url_evaluator: str = "postgresql://pec:pec_secret@postgres:5432/pec_evaluator"
    ollama_base_url:        str = "http://ollama:11434"
    ollama_embedding_model: str = "nomic-embed-text"
    evaluator_service_url:  str = "http://ms-014-evaluator:8000"
    # Optional bearer-token guard (leave empty to disable)
    mcp_api_key:            str = ""
    server_host:            str = "0.0.0.0"
    server_port:            int = 8000

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
