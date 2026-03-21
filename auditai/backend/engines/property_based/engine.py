"""
Property-Based Testing Engine — Level 3a of the testing pyramid.
Generates diverse inputs (valid, invalid, edge-case) and tests them against
registered properties. Neural VAE enhances corner-case generation.
"""
import time
import importlib
import traceback
from typing import List
from engines.base import BaseEngine, EngineContext, EngineResult, FindingData, StackInfo
from engines.property_based.neural import PropertyNeuralAssistant
from engines.property_based.generators import (
    gen_monetary_edge_cases, gen_date_edge_cases, gen_invalid_inputs
)


class PropertyEngine(BaseEngine):
    name = "property_based"
    version = "1.0.0"
    pyramid_level = 3

    def _init_neural(self):
        return PropertyNeuralAssistant()

    def run(self, context: EngineContext) -> EngineResult:
        start = time.time()
        findings = []
        insights = []

        # Collect test inputs
        test_inputs = []
        test_inputs.extend(gen_invalid_inputs())
        test_inputs.extend([str(v) for v in gen_monetary_edge_cases()])
        test_inputs.extend([str(d) for d in gen_date_edge_cases()])

        # Neural-generated additional candidates
        neural_candidates = self.neural.generate_candidates(test_inputs)
        test_inputs.extend(neural_candidates)

        # Run built-in property checks on config-provided function references
        properties = context.config.get("properties", [])
        failures = []

        for prop in properties:
            try:
                module_path, func_name = prop["function"].rsplit(".", 1)
                mod = importlib.import_module(module_path)
                func = getattr(mod, func_name)

                for inp in test_inputs:
                    try:
                        result = func(inp)
                        if result is False:
                            failures.append({
                                "property": prop.get("name", func_name),
                                "input": inp,
                                "expected": "True (property must hold)",
                                "actual": "False",
                            })
                    except Exception as e:
                        failures.append({
                            "property": prop.get("name", func_name),
                            "input": inp,
                            "exception": str(e),
                            "traceback": traceback.format_exc()[:500],
                        })
            except Exception as e:
                insights.append(f"Could not load property {prop}: {e}")

        # Convert failures to findings
        for failure in failures:
            neural_score = self.neural.score({"input": failure.get("input", "")})
            findings.append(FindingData(
                engine=self.name,
                pyramid_level=self.pyramid_level,
                severity="HIGH" if neural_score > 0.7 else "MEDIUM",
                category="property_violation",
                title=f"Property violated: {failure['property']}",
                description=failure.get("exception") or failure.get("expected", ""),
                evidence={
                    "input": str(failure.get("input", ""))[:200],
                    "failure": failure,
                },
                seed=str(failure.get("input", "")),
                neural_score=neural_score,
            ))

        score = max(0, 100 - len(findings) * 10)
        elapsed_ms = int((time.time() - start) * 1000)

        insights.append(self.neural.explain({"input": test_inputs[0] if test_inputs else ""}))
        insights.append(f"Tested {len(test_inputs)} inputs across {len(properties)} properties")

        return EngineResult(
            engine=self.name,
            pyramid_level=self.pyramid_level,
            findings=findings,
            score=score,
            neural_insights=insights,
            summary=f"{len(failures)} property violation(s) found across {len(test_inputs)} inputs",
            execution_time_ms=elapsed_ms,
        )
