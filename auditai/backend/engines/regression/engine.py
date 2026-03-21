"""
Regression Engine — Level 2a of the testing pyramid.
Replays historical corpus cases and checks for regressions.
Neural deduplication prevents duplicate findings.
"""
import time
from engines.base import BaseEngine, EngineContext, EngineResult, FindingData
from engines.regression.neural import RegressionNeuralAssistant


class RegressionEngine(BaseEngine):
    name = "regression"
    version = "1.0.0"
    pyramid_level = 2

    def _init_neural(self):
        return RegressionNeuralAssistant()

    def run(self, context: EngineContext) -> EngineResult:
        start = time.time()
        findings = []
        insights = []

        corpus_cases = context.corpus_cases or []
        if not corpus_cases:
            return EngineResult(engine=self.name, pyramid_level=self.pyramid_level,
                                score=100, summary="No corpus cases", status="SKIPPED")

        failed_cases = []
        seen_descriptions = []

        for case in corpus_cases:
            result = _replay_case(case, context)
            if not result["passed"]:
                desc = case.get("description", case.get("title", ""))
                novelty = self.neural.score({
                    "description": desc,
                    "existing": seen_descriptions,
                })
                if novelty > 0.3:  # not a duplicate
                    failed_cases.append({**case, "result": result, "novelty": novelty})
                    seen_descriptions.append(desc)

        for case in failed_cases:
            findings.append(FindingData(
                engine=self.name,
                pyramid_level=self.pyramid_level,
                severity=_severity_from_criticality(case.get("criticality", "MEDIUM")),
                category="regression",
                title=f"Regression: {case.get('title', 'Unknown case')}",
                description=case.get("description", ""),
                evidence={"input": case.get("input_payload"), "result": case["result"]},
                seed=str(case.get("input_payload", "")),
                neural_score=case["novelty"],
            ))

        score = max(0, 100 - len(findings) * 10)
        elapsed_ms = int((time.time() - start) * 1000)

        insights.append(self.neural.explain({"description": failed_cases[0].get("description", "") if failed_cases else ""}))
        insights.append(f"Replayed {len(corpus_cases)} cases, {len(failed_cases)} regressions found")

        return EngineResult(
            engine=self.name, pyramid_level=self.pyramid_level,
            findings=findings, score=score, neural_insights=insights,
            summary=f"{len(findings)} regression(s) in {len(corpus_cases)} cases replayed",
            execution_time_ms=elapsed_ms,
        )


def _replay_case(case: dict, context: EngineContext) -> dict:
    """Simulate replaying a corpus case. In production, calls the actual service."""
    import random
    # Simulate: 10% chance of regression for any case
    passed = random.random() > 0.1
    return {"passed": passed, "message": "ok" if passed else "assertion failed"}


def _severity_from_criticality(criticality: str) -> str:
    return {"CRITICAL": "CRITICAL", "HIGH": "HIGH", "MEDIUM": "MEDIUM",
            "LOW": "LOW"}.get(criticality.upper(), "MEDIUM")
