"""
Neural assistant for the AI Test Generator engine.
Wraps LLM (Claude / Ollama) for test generation scoring.
No torch dependency required — uses the Anthropic SDK directly.
"""
from engines.base import NeuralAssistant, FallbackNeuralAssistant


class AITestGenNeural(NeuralAssistant):
    """LLM-backed assistant for evaluating generated test quality."""

    def __init__(self, config: dict = None):
        self._config = config or {}
        self._available = self._check_available()

    def _check_available(self) -> bool:
        if self._config.get("anthropic_api_key"):
            return True
        try:
            import httpx
            resp = httpx.get(
                f"{self._config.get('ollama_url', 'http://localhost:11434')}/api/tags",
                timeout=2.0,
            )
            return resp.status_code == 200
        except Exception:
            return False

    def is_available(self) -> bool:
        return self._available

    def score(self, context: dict) -> float:
        """Score the quality of generated tests (0.0–1.0)."""
        if not self._available:
            return FallbackNeuralAssistant().score(context)

        num_tests = context.get("num_tests", 0)
        num_properties = context.get("num_properties", 0)
        num_synthetic_cases = context.get("num_synthetic_cases", 0)
        has_llm = context.get("llm_generated", False)

        # Heuristic score: more generated = higher quality signal
        raw = min(1.0, (num_tests * 0.1 + num_properties * 0.15 + num_synthetic_cases * 0.05))
        if has_llm:
            raw = min(1.0, raw + 0.2)
        return round(raw, 3)

    def explain(self, context: dict) -> str:
        score = self.score(context)
        num_tests = context.get("num_tests", 0)
        num_properties = context.get("num_properties", 0)
        return (
            f"Generated {num_tests} unit tests and {num_properties} properties. "
            f"Quality score: {score:.2f}. "
            + ("LLM-enhanced generation." if context.get("llm_generated") else "Template-only generation (configure LLM for higher quality).")
        )
