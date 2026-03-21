"""
Regression Neural Assistant — Sentence-BERT embedding deduplication.
Detects if a new failure is a known variant of an existing corpus case.
"""
from engines.base import NeuralAssistant


class RegressionNeuralAssistant(NeuralAssistant):
    """Embedding-based deduplication using Sentence-BERT cosine similarity."""

    def __init__(self):
        self._model = None
        self._available = False
        try:
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer("all-MiniLM-L6-v2")
            self._available = True
        except Exception:
            pass

    def is_available(self) -> bool:
        return self._available

    def score(self, context: dict) -> float:
        """Return novelty score: 1.0 = completely new, 0.0 = exact duplicate."""
        if not self._available:
            return 0.8
        try:
            import numpy as np
            desc = context.get("description", "")
            existing_descs = context.get("existing", [])
            if not desc or not existing_descs:
                return 1.0
            embs = self._model.encode([desc] + existing_descs)
            new_emb = embs[0]
            old_embs = embs[1:]
            sims = [float(np.dot(new_emb, e) / (np.linalg.norm(new_emb) * np.linalg.norm(e)))
                    for e in old_embs]
            max_sim = max(sims) if sims else 0.0
            return 1.0 - max_sim  # novelty = 1 - max_similarity
        except Exception:
            return 0.8

    def explain(self, context: dict) -> str:
        score = self.score(context)
        if score < 0.2:
            return f"Regression model: likely duplicate ({score:.2f} novelty)"
        elif score < 0.6:
            return f"Regression model: variant of known issue ({score:.2f} novelty)"
        return f"Regression model: new failure ({score:.2f} novelty)"
