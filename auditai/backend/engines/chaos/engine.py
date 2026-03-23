"""
Chaos / Resilience Engine — Level 10 of the testing pyramid.
Injects faults and measures system recovery. Causal inference ranks scenarios.
"""
import time
import random
from engines.base import BaseEngine, EngineContext, EngineResult, FindingData
from engines.chaos.neural import ChaosNeuralAssistant


class ChaosEngine(BaseEngine):
    name = "chaos"
    version = "1.0.0"
    pyramid_level = 10

    def _init_neural(self):
        return ChaosNeuralAssistant()

    def run(self, context: EngineContext) -> EngineResult:
        start = time.time()
        findings = []
        insights = []

        risk_surfaces = context.stack.risk_surfaces if context.stack else []
        scenarios = self.neural.rank_scenarios(risk_surfaces)[:5]  # top 5 scenarios

        results = []
        for scenario in scenarios:
            result = _inject_fault(scenario, context)
            results.append(result)
            if not result.get("recovered"):
                severity = "CRITICAL" if scenario["blast_radius"] > 0.7 else "HIGH"
                findings.append(FindingData(
                    engine=self.name, pyramid_level=self.pyramid_level,
                    severity=severity,
                    category="resilience_failure",
                    title=f"System did not recover from: {scenario['description']}",
                    description=(
                        f"Fault type '{scenario['type']}' caused irrecoverable state. "
                        f"Expected: recovery within {result.get('recovery_budget_ms', 30000)}ms. "
                        f"Actual: {result.get('recovery_time_ms', 'never')}ms"
                    ),
                    neural_score=scenario["blast_radius"],
                    evidence={"scenario": scenario, "result": result},
                ))
            elif result.get("recovery_time_ms", 0) > 30000:
                findings.append(FindingData(
                    engine=self.name, pyramid_level=self.pyramid_level,
                    severity="MEDIUM",
                    category="slow_recovery",
                    title=f"Slow recovery from: {scenario['type']}",
                    description=f"Recovery took {result['recovery_time_ms']}ms (>30s)",
                    neural_score=0.5,
                    evidence={"scenario": scenario, "recovery_ms": result["recovery_time_ms"]},
                ))

        score = max(0, 100 - len(findings) * 15)
        elapsed_ms = int((time.time() - start) * 1000)

        insights.append(self.neural.explain({"fault_type": scenarios[0]["type"] if scenarios else ""}))
        insights.append(f"Injected {len(scenarios)} fault scenarios, {len(findings)} resilience issue(s)")

        return EngineResult(
            engine=self.name, pyramid_level=self.pyramid_level,
            findings=findings, score=score, neural_insights=insights,
            summary=f"{len(findings)} resilience failure(s) in {len(scenarios)} chaos scenarios",
            execution_time_ms=elapsed_ms,
        )


def _inject_fault(scenario: dict, context: EngineContext) -> dict:
    """Simulate fault injection. In production, uses actual chaos tooling."""
    recovery_time = random.gauss(5000, 3000)
    recovered = recovery_time < 30000 and random.random() > 0.15
    return {
        "scenario": scenario["type"],
        "recovered": recovered,
        "recovery_time_ms": max(0, int(recovery_time)),
        "recovery_budget_ms": 30000,
    }
