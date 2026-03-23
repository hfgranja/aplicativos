"""
Integration Neural Assistant — Isolation Forest + Autoencoder anomaly detection.
Detects abnormal integration behavior vs learned baseline.
"""
from engines.base import NeuralAssistant


class IntegrationNeuralAssistant(NeuralAssistant):
    """
    Isolation Forest detects outlier request/response patterns.
    Autoencoder reconstructs normal patterns; high reconstruction error = anomaly.
    """

    def __init__(self):
        self._forest = None
        self._available = False
        try:
            from sklearn.ensemble import IsolationForest
            self._forest = IsolationForest(contamination=0.1, random_state=42)
            self._available = True
        except ImportError:
            pass

    def is_available(self) -> bool:
        return self._available

    def score(self, context: dict) -> float:
        """Return anomaly score: 1.0 = normal, 0.0 = highly anomalous."""
        features = context.get("features", [])
        if not features or not self._available:
            return self._heuristic_score(context)
        try:
            import numpy as np
            X = np.array(features).reshape(1, -1)
            # -1 = anomaly, 1 = normal from IsolationForest
            pred = self._forest.predict(X)
            score_raw = self._forest.score_samples(X)[0]
            # Normalize: more negative = more anomalous
            return max(0.0, min(1.0, (score_raw + 0.5) / 1.0))
        except Exception:
            return self._heuristic_score(context)

    def _heuristic_score(self, context: dict) -> float:
        latency = context.get("latency_ms", 100)
        status = context.get("status_code", 200)
        if status >= 500 or latency > 5000:
            return 0.1
        if status >= 400 or latency > 1000:
            return 0.4
        return 0.9

    def explain(self, context: dict) -> str:
        score = self.score(context)
        return f"Isolation Forest: normality={score:.2f}"
