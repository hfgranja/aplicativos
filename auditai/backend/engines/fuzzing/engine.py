"""
Fuzzing Engine — Level 3b of the testing pyramid.
Neural-guided (DQN) fuzzer that mutates inputs to find crashes, timeouts, and anomalies.
"""
import time
import random
import string
from engines.base import BaseEngine, EngineContext, EngineResult, FindingData
from engines.fuzzing.neural import FuzzingNeuralAssistant


class FuzzingEngine(BaseEngine):
    name = "fuzzing"
    version = "1.0.0"
    pyramid_level = 3

    def _init_neural(self):
        return FuzzingNeuralAssistant()

    def run(self, context: EngineContext) -> EngineResult:
        start = time.time()
        findings = []
        insights = []

        budget_seconds = context.config.get("budget_seconds", 60)
        targets = context.config.get("targets", [{"type": "generic"}])
        corpus = context.corpus_cases or []

        # Build initial corpus
        seeds = [str(c.get("input_payload", "")) for c in corpus if c.get("input_payload")]
        seeds += _default_seeds()

        crashes = []
        iterations = 0
        max_iterations = min(500, budget_seconds * 10)

        while iterations < max_iterations:
            # Neural operator selection
            operator = self.neural.select_operator()
            seed = random.choice(seeds) if seeds else ""
            mutated = _mutate(seed, operator)

            result = _execute_fuzz(mutated, context)
            iterations += 1

            if result.get("crash"):
                crashes.append({"input": mutated, "error": result["error"], "operator": operator})
                self.neural.update(operator, 1.0)  # high reward for crash
                seeds.append(mutated)
            elif result.get("timeout"):
                crashes.append({"input": mutated, "error": "timeout", "operator": operator})
                self.neural.update(operator, 0.8)
            elif result.get("anomaly"):
                crashes.append({"input": mutated, "error": result.get("anomaly"), "operator": operator})
                self.neural.update(operator, 0.5)
            else:
                self.neural.update(operator, 0.1)

        for crash in crashes[:20]:
            findings.append(FindingData(
                engine=self.name, pyramid_level=self.pyramid_level,
                severity="HIGH" if "crash" in crash.get("error", "").lower() else "MEDIUM",
                category="fuzzing_crash" if "crash" in crash.get("error", "").lower() else "fuzzing_anomaly",
                title=f"Fuzzing: {crash['error'][:80]}",
                description=f"Input caused {crash['error']} using operator '{crash['operator']}'",
                seed=str(crash["input"])[:500],
                evidence={"input": str(crash["input"])[:200], "error": crash["error"]},
                neural_score=0.8,
            ))

        score = max(0, 100 - len(crashes) * 8)
        elapsed_ms = int((time.time() - start) * 1000)

        insights.append(self.neural.explain({}))
        insights.append(f"Ran {iterations} fuzz iterations, {len(crashes)} crashes/anomalies found")

        return EngineResult(
            engine=self.name, pyramid_level=self.pyramid_level,
            findings=findings, score=score, neural_insights=insights,
            summary=f"{len(crashes)} fuzzing issue(s) in {iterations} iterations",
            evidence={"iterations": iterations, "crashes": len(crashes)},
            execution_time_ms=elapsed_ms,
        )


def _default_seeds() -> list:
    return ["", "null", "0", "-1", "a" * 1000, "<script>", "' OR 1=1", "../../../etc/passwd",
            "{{7*7}}", "\x00", "9" * 50]


def _mutate(seed: str, operator: str) -> str:
    s = list(str(seed))
    if not s:
        s = list("a")
    if operator == "bit_flip" and s:
        i = random.randint(0, len(s) - 1)
        s[i] = chr(ord(s[i]) ^ (1 << random.randint(0, 7)) & 0xFF)
    elif operator == "append":
        s += list(''.join(random.choices(string.printable, k=random.randint(1, 50))))
    elif operator == "truncate" and len(s) > 1:
        s = s[:random.randint(0, len(s) - 1)]
    elif operator == "insert_special":
        special = random.choice(["<script>", "' OR 1=1", "\x00", "{{7*7}}", "../../../", "%00"])
        pos = random.randint(0, len(s))
        s = s[:pos] + list(special) + s[pos:]
    elif operator == "arithmetic":
        s = list(str(random.choice([-1, 0, 2**31 - 1, 2**31, -2**31, 9999999999])))
    elif operator == "interesting_int":
        s = list(str(random.choice([0, 1, -1, 127, 128, 255, 256, 65535, 65536])))
    elif operator == "duplicate":
        s = s * 2
    elif operator == "random_bytes":
        s = [chr(random.randint(0, 127)) for _ in range(random.randint(1, 100))]
    return ''.join(s)[:2000]


def _execute_fuzz(mutated: str, context: EngineContext) -> dict:
    """Simulate fuzzing execution. In production, calls actual target."""
    # Simulate crash probability
    crash_triggers = ["<script>", "' OR", "\x00", "{{", "../", "%00"]
    if any(t in mutated for t in crash_triggers):
        if random.random() < 0.3:
            return {"crash": True, "error": "parser exception on malformed input"}
    if len(mutated) > 500 and random.random() < 0.1:
        return {"timeout": True, "error": "timeout"}
    return {"ok": True}
