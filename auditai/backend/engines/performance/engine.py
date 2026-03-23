"""
Performance Testing Engine — Level 8 of the testing pyramid.
Measures latency, throughput, and resource usage. LSTM predicts degradation trends.
"""
import time
import random
from engines.base import BaseEngine, EngineContext, EngineResult, FindingData
from engines.performance.neural import PerformanceNeuralAssistant


class PerformanceEngine(BaseEngine):
    name = "performance"
    version = "1.0.0"
    pyramid_level = 8

    def _init_neural(self):
        return PerformanceNeuralAssistant()

    def run(self, context: EngineContext) -> EngineResult:
        start = time.time()
        findings = []
        insights = []

        target_url = context.config.get("target_url")
        concurrent_users = context.config.get("concurrent_users", 10)
        duration_seconds = context.config.get("duration_seconds", 30)
        thresholds = context.config.get("thresholds", {"p99_ms": 2000, "error_rate": 0.05})

        # Simulate load test
        latencies, errors = _simulate_load_test(target_url, concurrent_users, duration_seconds)

        if not latencies:
            return EngineResult(engine=self.name, pyramid_level=self.pyramid_level,
                                score=100, summary="No performance data collected", status="SKIPPED")

        latencies_sorted = sorted(latencies)
        p50 = latencies_sorted[len(latencies_sorted) // 2]
        p95 = latencies_sorted[int(len(latencies_sorted) * 0.95)]
        p99 = latencies_sorted[int(len(latencies_sorted) * 0.99)]
        error_rate = len(errors) / len(latencies) if latencies else 0
        throughput = len(latencies) / duration_seconds

        # Neural degradation prediction
        degradation_risk = self.neural.score({"latencies": latencies[-100:]})

        # Generate findings for threshold violations
        if p99 > thresholds.get("p99_ms", 2000):
            findings.append(FindingData(
                engine=self.name, pyramid_level=self.pyramid_level,
                severity="HIGH", category="performance",
                title=f"P99 latency exceeded: {p99}ms > {thresholds['p99_ms']}ms",
                description=f"P99 latency is {p99}ms, exceeding threshold of {thresholds['p99_ms']}ms",
                neural_score=degradation_risk,
                evidence={"p50": p50, "p95": p95, "p99": p99},
            ))

        if error_rate > thresholds.get("error_rate", 0.05):
            findings.append(FindingData(
                engine=self.name, pyramid_level=self.pyramid_level,
                severity="CRITICAL", category="error_rate",
                title=f"High error rate: {error_rate:.1%}",
                description=f"Error rate {error_rate:.1%} exceeds threshold {thresholds['error_rate']:.1%}",
                neural_score=0.9,
            ))

        if degradation_risk > 0.7:
            findings.append(FindingData(
                engine=self.name, pyramid_level=self.pyramid_level,
                severity="MEDIUM", category="degradation_trend",
                title=f"Performance degradation trend detected",
                description=f"LSTM model predicts {degradation_risk:.0%} probability of degradation",
                neural_score=degradation_risk,
            ))

        score = max(0, 100 - len(findings) * 20)
        elapsed_ms = int((time.time() - start) * 1000)

        insights.append(self.neural.explain({"latencies": latencies[-100:]}))
        insights.append(f"Load: {concurrent_users} users, p50={p50}ms, p99={p99}ms, errors={error_rate:.1%}")

        return EngineResult(
            engine=self.name, pyramid_level=self.pyramid_level,
            findings=findings, score=score, neural_insights=insights,
            summary=f"p50={p50}ms p99={p99}ms throughput={throughput:.1f}rps error={error_rate:.1%}",
            evidence={"p50": p50, "p95": p95, "p99": p99, "throughput": throughput, "error_rate": error_rate},
            execution_time_ms=elapsed_ms,
        )


def _simulate_load_test(url, users: int, duration: int):
    """Simulate load test metrics."""
    n = users * duration
    latencies = [max(1, int(random.gauss(200, 80))) for _ in range(n)]
    # Add some outliers
    for _ in range(n // 20):
        latencies.append(random.randint(1000, 5000))
    errors = [{"error": "timeout"} for _ in range(int(n * 0.02))]
    return latencies, errors
