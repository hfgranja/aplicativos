"""Generate text embeddings using Ollama /api/embeddings endpoint."""
import logging

import httpx

logger = logging.getLogger(__name__)

# nomic-embed-text produces 768-dim vectors; adjust if using a different model
EMBEDDING_DIM = 768


def embed(text: str, base_url: str, model: str) -> list[float]:
    """Return embedding vector for *text* using Ollama embedding model."""
    payload = {"model": model, "prompt": text}
    try:
        resp = httpx.post(f"{base_url}/api/embeddings", json=payload, timeout=60.0)
        resp.raise_for_status()
        return resp.json()["embedding"]
    except Exception as exc:
        logger.error("Ollama embedding failed: %s", exc)
        raise


def embed_batch(texts: list[str], base_url: str, model: str) -> list[list[float]]:
    return [embed(t, base_url, model) for t in texts]
