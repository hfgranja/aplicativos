"""
SAST Neural Assistant — CodeBERT-based vulnerability probability scorer.
Delegates to DeepVulnClassifier from engines.neural when available,
falls back to rule-based scoring when PyTorch / transformers are unavailable.
"""
from engines.base import NeuralAssistant, FallbackNeuralAssistant


class SASTNeuralAssistant(NeuralAssistant):
    """
    Uses DeepVulnClassifier (CodeBERT fine-tuned on BigVul + NVD/CWE) to
    score vulnerability probability.

    Architecture: microsoft/codebert-base with two classification heads:
    - vuln_head: binary vulnerability probability
    - cwe_head:  multi-label CWE category prediction (Top-25)

    Falls back to heuristic rule-based scoring when ML stack is unavailable.
    """

    def __init__(self):
        self._classifier = None
        self._available = False
        self._load_model()

    def _load_model(self):
        try:
            from engines.neural.models import ModelRegistry
            self._classifier = ModelRegistry.get_instance().get_classifier()
            self._available = True
        except Exception:
            self._available = False

    def is_available(self) -> bool:
        return self._available

    def score(self, context: dict) -> float:
        code = context.get("code_snippet", "")
        if not code:
            return 0.0
        if not self._available or self._classifier is None:
            return FallbackNeuralAssistant().score(context)
        try:
            pred = self._classifier.predict(code)
            return round(pred.confidence if pred.is_vulnerable else 1.0 - pred.confidence, 4)
        except Exception:
            return FallbackNeuralAssistant().score(context)

    def explain(self, context: dict) -> str:
        code = context.get("code_snippet", "")
        if not self._available or self._classifier is None or not code:
            return FallbackNeuralAssistant().explain(context)
        try:
            pred = self._classifier.predict(code)
            score = pred.confidence if pred.is_vulnerable else 1.0 - pred.confidence
            cwe_str = (
                f" — top CWE: {pred.cwe_predictions[0]}" if pred.cwe_predictions else ""
            )
            if score > 0.8:
                level = "HIGH"
            elif score > 0.5:
                level = "MODERATE"
            else:
                level = "LOW"
            return (
                f"DeepVulnClassifier ({pred.severity or level}): "
                f"vulnerability probability {score:.0%}{cwe_str}. "
                f"{pred.explanation or ''}"
            ).strip()
        except Exception:
            return FallbackNeuralAssistant().explain(context)

    def get_cwe_predictions(self, code: str) -> list[str]:
        """Return predicted CWE IDs for a code snippet."""
        if not self._available or self._classifier is None:
            return []
        try:
            pred = self._classifier.predict(code)
            return pred.cwe_predictions
        except Exception:
            return []
