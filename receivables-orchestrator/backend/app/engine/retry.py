"""Motor de retry (secao 3/6/9 do design doc): backoff controlado com
limite de tentativas antes de acionar fallback para outro meio."""
from __future__ import annotations


def should_retry(attempt_number: int, max_retries: int) -> bool:
    return attempt_number <= max_retries


def backoff_seconds(attempt_number: int, base_seconds: int) -> int:
    # Backoff exponencial simples com teto, evitando fadiga/spam no cliente.
    return min(base_seconds * (2 ** (attempt_number - 1)), 600)
