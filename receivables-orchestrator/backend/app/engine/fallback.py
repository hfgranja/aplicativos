"""Motor de fallback (secao 3/6 do design doc): decide o proximo meio quando
o atual falha ou expira, respeitando a sequencia configurada pelo merchant
e o numero maximo de saltos (hops)."""
from __future__ import annotations


def next_fallback_method(sequence: list[str], failed_method: str, hop_index: int, max_hops: int) -> str | None:
    if hop_index + 1 >= max_hops:
        return None
    if failed_method not in sequence:
        return sequence[0] if sequence else None
    idx = sequence.index(failed_method)
    if idx + 1 < len(sequence):
        return sequence[idx + 1]
    return None
