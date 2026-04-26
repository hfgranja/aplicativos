"""Smoke test — verifies all PEC microservices health endpoints are responding."""
import httpx
import pytest

SERVICES = [
    ("identity",      "http://localhost:8001"),
    ("school",        "http://localhost:8002"),
    ("observation",   "http://localhost:8003"),
    ("audio",         "http://localhost:8004"),
    ("transcription", "http://localhost:8005"),
    ("ai-feedback",   "http://localhost:8006"),
    ("feedback",      "http://localhost:8007"),
    ("pdf-export",    "http://localhost:8008"),
    ("audit",         "http://localhost:8009"),
    ("consent",       "http://localhost:8010"),
]


@pytest.mark.parametrize("name,base_url", SERVICES)
def test_service_healthy(name: str, base_url: str):
    try:
        r = httpx.get(f"{base_url}/health", timeout=5)
        assert r.status_code == 200, f"{name} returned {r.status_code}"
        body = r.json()
        assert body.get("status") == "ok", f"{name} health body: {body}"
    except httpx.ConnectError:
        pytest.skip(f"{name} not reachable — run docker compose up first")
