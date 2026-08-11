"""Shared resilient HTTP helper for provider adapters (spec seção 51).

Short timeout + single retry with backoff; raises ProviderUnavailableError
on any failure so callers can fall through the ProviderRouter chain instead
of crashing the request.
"""
from __future__ import annotations

import logging
import time

import httpx

from app.providers.base import ProviderUnavailableError

logger = logging.getLogger("agroprofit.providers")

DEFAULT_TIMEOUT = 8.0


def get_json(url: str, params: dict | None = None, timeout: float = DEFAULT_TIMEOUT, retries: int = 1) -> dict:
    last_exc: Exception | None = None
    for attempt in range(retries + 1):
        try:
            with httpx.Client(timeout=timeout) as client:
                resp = client.get(url, params=params)
                resp.raise_for_status()
                return resp.json()
        except Exception as exc:  # noqa: BLE001 — provider adapters must never propagate raw errors
            last_exc = exc
            logger.warning("provider http call failed (attempt %s/%s) %s: %s", attempt + 1, retries + 1, url, exc)
            if attempt < retries:
                time.sleep(0.5 * (attempt + 1))
    raise ProviderUnavailableError(f"GET {url} failed: {last_exc}") from last_exc
