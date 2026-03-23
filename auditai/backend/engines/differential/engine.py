"""
Differential Testing Engine — Level 6 of the testing pyramid.
Runs same inputs through two implementations (baseline vs current) and compares outputs.
Used for legacy modernization validation and AI-generated code verification.
"""
import time
from engines.base import BaseEngine, EngineContext, EngineResult, FindingData
from engines.differential.neural import DifferentialNeuralAssistant


class DifferentialEngine(BaseEngine):
    name = "differential"
    version = "1.0.0"
    pyramid_level = 6

    def _init_neural(self):
        return DifferentialNeuralAssistant()

    def run(self, context: EngineContext) -> EngineResult:
        start = time.time()
        findings = []
        insights = []

        corpus_cases = context.corpus_cases or []
        tolerance = context.config.get("tolerance", 0.001)
        baseline_url = context.config.get("baseline_url")
        current_url = context.config.get("current_url")

        if not corpus_cases:
            return EngineResult(engine=self.name, pyramid_level=self.pyramid_level,
                                score=100, summary="No test cases", status="SKIPPED")

        divergences = []
        for case in corpus_cases:
            inp = case.get("input_payload")
            result_a = _call_impl(baseline_url, inp, "baseline")
            result_b = _call_impl(current_url, inp, "current")

            similarity = self.neural.score({
                "output_a": result_a.get("output"),
                "output_b": result_b.get("output"),
                "tolerance": tolerance,
            })

            if similarity < 0.95:
                divergences.append({
                    "case": case.get("title", ""),
                    "input": inp,
                    "output_a": result_a,
                    "output_b": result_b,
                    "similarity": similarity,
                })

        for div in divergences:
            neural_score = 1.0 - div["similarity"]
            findings.append(FindingData(
                engine=self.name, pyramid_level=self.pyramid_level,
                severity="CRITICAL" if neural_score > 0.5 else "HIGH",
                category="functional_divergence",
                title=f"Output divergence: {div['case']}",
                description=f"Outputs differ with similarity={div['similarity']:.2f}",
                evidence={
                    "input": str(div["input"])[:200],
                    "output_baseline": str(div["output_a"])[:200],
                    "output_current": str(div["output_b"])[:200],
                },
                neural_score=neural_score,
            ))

        score = max(0, 100 - len(divergences) * 15)
        elapsed_ms = int((time.time() - start) * 1000)

        insights.append(self.neural.explain({"output_a": None, "output_b": None}))
        insights.append(f"Compared {len(corpus_cases)} cases, {len(divergences)} divergence(s)")

        return EngineResult(
            engine=self.name, pyramid_level=self.pyramid_level,
            findings=findings, score=score, neural_insights=insights,
            summary=f"{len(divergences)} functional divergence(s) found",
            execution_time_ms=elapsed_ms,
        )


def _call_impl(url, payload, label: str) -> dict:
    """Call an implementation endpoint. Simulated if URL not provided."""
    import random
    if not url:
        # Simulate with small random drift
        return {"output": {"value": 100 + random.uniform(-5, 5), "status": "ok"}}
    try:
        import httpx
        r = httpx.post(url, json=payload, timeout=10.0)
        return {"output": r.json(), "status_code": r.status_code}
    except Exception as e:
        return {"output": None, "error": str(e)}
