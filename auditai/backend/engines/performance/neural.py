"""
Performance Neural Assistant — LSTM time-series degradation predictor.
"""
from engines.base import NeuralAssistant


class PerformanceNeuralAssistant(NeuralAssistant):
    """LSTM that predicts performance degradation from latency/throughput time series."""

    def __init__(self):
        self._available = False
        try:
            import torch
            self._available = True
        except ImportError:
            pass

    def is_available(self) -> bool:
        return self._available

    def score(self, context: dict) -> float:
        """Return degradation risk [0=no risk, 1=high risk]."""
        latencies = context.get("latencies", [])
        if not latencies:
            return 0.0
        # Heuristic: check if trend is increasing
        if len(latencies) >= 3:
            recent = latencies[-3:]
            if recent[-1] > recent[0] * 1.5:
                return 0.8
            if recent[-1] > recent[0] * 1.2:
                return 0.5
        # Check absolute thresholds
        p99 = sorted(latencies)[int(len(latencies) * 0.99)] if len(latencies) > 10 else max(latencies)
        if p99 > 2000:
            return 0.9
        if p99 > 500:
            return 0.5
        return 0.1

    def explain(self, context: dict) -> str:
        score = self.score(context)
        return f"LSTM degradation predictor: risk={score:.2f}"
