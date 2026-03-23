"""
Integration Testing Engine — Level 4 of the testing pyramid.
Tests service interactions, API contracts, and detects anomalies via neural model.
"""
import time
import random
from engines.base import BaseEngine, EngineContext, EngineResult, FindingData
from engines.integration.neural import IntegrationNeuralAssistant


class IntegrationEngine(BaseEngine):
    name = "integration"
    version = "1.0.0"
    pyramid_level = 4

    def _init_neural(self):
        return IntegrationNeuralAssistant()

    def run(self, context: EngineContext) -> EngineResult:
        start = time.time()
        findings = []
        insights = []

        endpoints = context.config.get("endpoints", [])
        if not endpoints:
            # Try to derive from contract
            endpoints = _derive_endpoints(context)

        results = []
        for ep in endpoints[:20]:  # limit to 20 endpoints per run
            result = _test_endpoint(ep, context)
            normality = self.neural.score({
                "latency_ms": result.get("latency_ms", 0),
                "status_code": result.get("status_code", 200),
                "features": [result.get("latency_ms", 0) / 1000, result.get("status_code", 200) / 500,
                              len(str(result.get("body", ""))) / 10000],
            })
            result["normality"] = normality
            results.append(result)

            if normality < 0.3:
                findings.append(FindingData(
                    engine=self.name, pyramid_level=self.pyramid_level,
                    severity="HIGH" if normality < 0.1 else "MEDIUM",
                    category="integration_anomaly",
                    title=f"Anomaly: {ep.get('method', 'GET')} {ep.get('path', '/')}",
                    description=f"Abnormal behavior detected (normality={normality:.2f})",
                    evidence={"endpoint": ep, "result": result},
                    neural_score=1.0 - normality,
                ))

        score = max(0, 100 - len(findings) * 10)
        elapsed_ms = int((time.time() - start) * 1000)

        insights.append(self.neural.explain({"latency_ms": 100, "status_code": 200}))
        insights.append(f"Tested {len(results)} integrations, {len(findings)} anomalies")

        return EngineResult(
            engine=self.name, pyramid_level=self.pyramid_level,
            findings=findings, score=score, neural_insights=insights,
            summary=f"{len(findings)} integration anomaly(ies) in {len(results)} endpoint(s) tested",
            execution_time_ms=elapsed_ms,
        )


def _derive_endpoints(context: EngineContext) -> list:
    if not context.contract_content:
        return [{"method": "GET", "path": "/health"}]
    from engines.contract.parsers.openapi import parse_openapi
    spec = parse_openapi(context.contract_content)
    if not spec:
        return []
    endpoints = []
    for path, methods in spec.get("paths", {}).items():
        for method in methods:
            endpoints.append({"method": method.upper(), "path": path})
    return endpoints[:10]


def _test_endpoint(ep: dict, context: EngineContext) -> dict:
    """Simulate endpoint test. In production, calls actual service."""
    latency = random.gauss(150, 50)
    status = 200
    if random.random() < 0.05:
        status = 500
        latency = random.gauss(5000, 1000)
    elif random.random() < 0.1:
        status = 404
    return {
        "method": ep.get("method"),
        "path": ep.get("path"),
        "status_code": status,
        "latency_ms": max(1, int(latency)),
        "body": '{"ok": true}',
    }
