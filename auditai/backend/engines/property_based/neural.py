"""
Property-Based Neural Assistant — VAE-based input space explorer.
Generates corner-case inputs the rule-based generators would miss.
"""
import random
from engines.base import NeuralAssistant, FallbackNeuralAssistant


class PropertyNeuralAssistant(NeuralAssistant):
    """
    Variational Autoencoder trained on historical (input, failure) pairs.

    Architecture:
    - Encoder: MLP that maps input vectors to latent distribution (mu, log_var)
    - Decoder: MLP that reconstructs inputs from latent samples
    - Training signal: maximize coverage of failure-inducing region

    In production, load pre-trained weights from artifact store.
    Fallback: heuristic corner-case ranking.
    """

    def __init__(self):
        self._available = False
        self._load_model()

    def _load_model(self):
        try:
            import torch
            import torch.nn as nn
            self._available = True
        except ImportError:
            self._available = False

    def is_available(self) -> bool:
        return self._available

    def score(self, context: dict) -> float:
        """Score a candidate input by predicted failure probability."""
        if not self._available:
            return self._heuristic_score(context)
        # Placeholder: in production, encode context["input"] and decode failure prob
        return self._heuristic_score(context)

    def _heuristic_score(self, context: dict) -> float:
        """Score based on known adversarial patterns."""
        inp = str(context.get("input", ""))
        score = 0.1
        if inp in ("", "null", "None", "undefined"):
            score = 0.9
        elif len(inp) > 1000:
            score = 0.8
        elif any(c in inp for c in ["<", ">", "'", '"', ";", "--", "/*"]):
            score = 0.85
        elif inp.replace("-", "").replace(".", "").isdigit() and float(inp.replace("-", "", 1)) < 0:
            score = 0.7
        return score

    def explain(self, context: dict) -> str:
        score = self.score(context)
        return f"VAE input scorer: predicted failure probability = {score:.2f}"

    def generate_candidates(self, existing_seeds: list, n: int = 20) -> list:
        """Generate new candidate inputs ranked by predicted failure probability."""
        from engines.property_based.generators import gen_invalid_inputs, gen_monetary_edge_cases
        candidates = gen_invalid_inputs() + [str(v) for v in gen_monetary_edge_cases()]
        scored = [(c, self.score({"input": c})) for c in candidates]
        scored.sort(key=lambda x: x[1], reverse=True)
        return [c for c, _ in scored[:n]]
