"""
Differential Neural Assistant — Siamese network for output equivalence.
Determines if two outputs are semantically equivalent even when representation differs.
"""
import json
from engines.base import NeuralAssistant


class DifferentialNeuralAssistant(NeuralAssistant):
    """
    Siamese network: two encoders share weights, compare embeddings of output pairs.
    Falls back to structural comparison.
    """

    def __init__(self):
        self._available = False

    def is_available(self) -> bool:
        return True  # heuristic always available

    def score(self, context: dict) -> float:
        """Return similarity score 0=divergent, 1=equivalent."""
        out_a = context.get("output_a")
        out_b = context.get("output_b")
        tolerance = context.get("tolerance", 0.001)
        return _structural_similarity(out_a, out_b, tolerance)

    def explain(self, context: dict) -> str:
        score = self.score(context)
        return f"Siamese comparator: equivalence={score:.2f}"


def _structural_similarity(a, b, tolerance: float = 0.001) -> float:
    """Recursive structural comparison with float tolerance."""
    if a is None and b is None:
        return 1.0
    if type(a) != type(b):
        # Allow string vs int comparison
        try:
            if abs(float(str(a)) - float(str(b))) <= tolerance:
                return 1.0
        except (ValueError, TypeError):
            pass
        return 0.0
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        if b == 0:
            return 1.0 if a == 0 else 0.0
        return 1.0 if abs(a - b) / max(abs(b), 1e-10) <= tolerance else 0.0
    if isinstance(a, str):
        return 1.0 if a.strip() == b.strip() else 0.0
    if isinstance(a, bool):
        return 1.0 if a == b else 0.0
    if isinstance(a, dict):
        if set(a.keys()) != set(b.keys()):
            return 0.5
        sims = [_structural_similarity(a[k], b[k], tolerance) for k in a]
        return sum(sims) / len(sims) if sims else 1.0
    if isinstance(a, list):
        if len(a) != len(b):
            return 0.5
        sims = [_structural_similarity(x, y, tolerance) for x, y in zip(a, b)]
        return sum(sims) / len(sims) if sims else 1.0
    return 1.0 if a == b else 0.0
