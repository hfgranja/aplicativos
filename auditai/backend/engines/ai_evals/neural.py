"""
Neural assistant for the AI Evals engine.
Uses sentence-transformers to score semantic consistency between
LLM outputs and reference contexts.
"""
from engines.base import NeuralAssistant, FallbackNeuralAssistant


class AIEvalsNeural(NeuralAssistant):
    """Sentence-BERT based consistency scorer for LLM outputs."""

    def __init__(self):
        self._model = None
        self._available = False
        try:
            from sentence_transformers import SentenceTransformer, util
            self._model = SentenceTransformer("all-MiniLM-L6-v2")
            self._util = util
            self._available = True
        except Exception:
            pass

    def is_available(self) -> bool:
        return self._available

    def score(self, context: dict) -> float:
        """
        Scores semantic consistency between LLM output and reference context.
        Returns 0.0 (fully inconsistent) to 1.0 (fully consistent).
        A high inconsistency score (low return value) indicates hallucination risk.
        """
        if not self._available:
            return FallbackNeuralAssistant().score(context)

        reference = context.get("reference_context", "")
        response = context.get("llm_response", "")
        if not reference or not response:
            return 0.5

        try:
            emb_ref = self._model.encode(reference, convert_to_tensor=True)
            emb_resp = self._model.encode(response, convert_to_tensor=True)
            similarity = float(self._util.cos_sim(emb_ref, emb_resp)[0][0])
            return max(0.0, min(1.0, similarity))
        except Exception:
            return 0.5

    def explain(self, context: dict) -> str:
        score = self.score(context)
        if score > 0.8:
            return f"High semantic consistency ({score:.2f}) between LLM output and reference context."
        elif score > 0.5:
            return f"Moderate consistency ({score:.2f}); review LLM output for unsupported claims."
        else:
            return f"Low consistency ({score:.2f}); LLM output diverges significantly from reference context — possible hallucination."
