"""
Contract Neural Assistant — Sentence-BERT semantic drift detector.
Detects semantic drift between contract versions beyond schema diffs.
"""
from engines.base import NeuralAssistant, FallbackNeuralAssistant


class ContractNeuralAssistant(NeuralAssistant):
    """
    Uses Sentence-BERT to compute semantic similarity between two contract descriptions.
    Low similarity = semantic drift even if schema types are unchanged.

    Model: sentence-transformers/all-MiniLM-L6-v2 (lightweight, fast)
    """

    def __init__(self):
        self._model = None
        self._available = False
        self._load_model()

    def _load_model(self):
        try:
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer("all-MiniLM-L6-v2")
            self._available = True
        except Exception:
            self._available = False

    def is_available(self) -> bool:
        return self._available

    def score(self, context: dict) -> float:
        """Return semantic similarity [0,1] between two descriptions. Low = drift."""
        if not self._available:
            return 1.0  # assume no drift if neural unavailable
        try:
            import numpy as np
            desc_a = context.get("description_a", "")
            desc_b = context.get("description_b", "")
            if not desc_a or not desc_b:
                return 1.0
            emb_a, emb_b = self._model.encode([desc_a, desc_b])
            similarity = float(np.dot(emb_a, emb_b) / (np.linalg.norm(emb_a) * np.linalg.norm(emb_b)))
            return max(0.0, min(1.0, similarity))
        except Exception:
            return 1.0

    def explain(self, context: dict) -> str:
        score = self.score(context)
        if score < 0.6:
            return f"Sentence-BERT: HIGH semantic drift ({score:.2f}) — field meaning may have changed"
        elif score < 0.85:
            return f"Sentence-BERT: MODERATE semantic similarity ({score:.2f}) — review recommended"
        return f"Sentence-BERT: LOW semantic drift ({score:.2f}) — fields appear semantically equivalent"

    def detect_field_drift(self, old_fields: dict, new_fields: dict) -> list:
        """Compare field descriptions between versions and flag semantic drift."""
        drifts = []
        for field_name in old_fields:
            if field_name in new_fields:
                old_desc = old_fields[field_name].get("description", "")
                new_desc = new_fields[field_name].get("description", "")
                if old_desc and new_desc:
                    sim = self.score({"description_a": old_desc, "description_b": new_desc})
                    if sim < 0.75:
                        drifts.append({
                            "field": field_name,
                            "similarity": sim,
                            "old_description": old_desc,
                            "new_description": new_desc,
                        })
        return drifts
