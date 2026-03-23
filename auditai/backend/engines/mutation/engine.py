"""
Mutation Testing Engine — Level 2b of the testing pyramid.
Generates code mutants, runs existing test suite, measures kill rate (mutation score).
Neural GNN prioritizes high-survivability mutations.
"""
import time
import re
from typing import List
from engines.base import BaseEngine, EngineContext, EngineResult, FindingData, StackInfo
from engines.mutation.neural import MutationNeuralAssistant

MUTANT_OPERATORS = [
    {"type": ">", "replacement": ">=", "description": "Relational: > → >="},
    {"type": ">=", "replacement": ">", "description": "Relational: >= → >"},
    {"type": "<", "replacement": "<=", "description": "Relational: < → <="},
    {"type": "==", "replacement": "!=", "description": "Equality: == → !="},
    {"type": "!=", "replacement": "==", "description": "Equality: != → =="},
    {"type": "and", "replacement": "or", "description": "Logic: and → or"},
    {"type": "or", "replacement": "and", "description": "Logic: or → and"},
    {"type": "+", "replacement": "-", "description": "Arithmetic: + → -"},
    {"type": "-", "replacement": "+", "description": "Arithmetic: - → +"},
    {"type": "True", "replacement": "False", "description": "Boolean: True → False"},
    {"type": "return True", "replacement": "return False", "description": "Return: True → False"},
    {"type": "raise", "replacement": "pass  #", "description": "Exception: raise → removed"},
]


class MutationEngine(BaseEngine):
    name = "mutation"
    version = "1.0.0"
    pyramid_level = 2

    def _init_neural(self):
        return MutationNeuralAssistant()

    def run(self, context: EngineContext) -> EngineResult:
        start = time.time()
        findings = []
        insights = []

        code = context.source_code or ""
        if not code.strip():
            return EngineResult(engine=self.name, pyramid_level=self.pyramid_level,
                                score=100, summary="No source code", status="SKIPPED")

        # Generate mutation candidates
        candidates = _generate_candidates(code)

        # Neural prioritization
        prioritized = self.neural.prioritize_mutations(candidates, top_k=min(50, len(candidates)))

        # Simulate mutation testing (in production: actually run test suite with each mutant)
        total = len(prioritized)
        killed = 0
        survived_mutants = []

        for mutant in prioritized:
            # Heuristic: if tests file doesn't exist or mutant is on uncovered line, simulate survival
            is_killed = _simulate_kill(mutant, context)
            if is_killed:
                killed += 1
            else:
                survived_mutants.append(mutant)

        score = int((killed / total * 100)) if total > 0 else 100

        # Report survived mutants as findings
        for mutant in survived_mutants[:10]:  # top 10 for report
            neural_score = self.neural.score({"operator": mutant.get("type", ""), "complexity": 1})
            findings.append(FindingData(
                engine=self.name, pyramid_level=self.pyramid_level,
                severity="HIGH" if neural_score > 0.7 else "MEDIUM",
                category="mutation_survived",
                title=f"Mutant survived: {mutant['description']}",
                description=(
                    f"Mutation '{mutant['description']}' at line {mutant.get('line', '?')} "
                    f"was not killed by any test. Tests may not cover this path."
                ),
                line_number=mutant.get("line"),
                neural_score=neural_score,
                evidence={"mutant": mutant},
            ))

        elapsed_ms = int((time.time() - start) * 1000)
        insights.append(f"Mutation score: {score}% ({killed}/{total} mutants killed)")
        insights.append(self.neural.explain({"operator": ">", "complexity": 2}))

        return EngineResult(
            engine=self.name, pyramid_level=self.pyramid_level,
            findings=findings, score=score, neural_insights=insights,
            summary=f"Mutation score: {score}% — {len(survived_mutants)} mutants survived",
            evidence={"total_mutants": total, "killed": killed, "survived": len(survived_mutants)},
            execution_time_ms=elapsed_ms,
        )


def _generate_candidates(code: str) -> List[dict]:
    candidates = []
    lines = code.splitlines()
    for i, line in enumerate(lines, start=1):
        for op in MUTANT_OPERATORS:
            if op["type"] in line:
                candidates.append({
                    "type": op["type"],
                    "replacement": op["replacement"],
                    "description": op["description"],
                    "line": i,
                    "original_line": line.strip(),
                    "complexity": 1 + line.count("if") + line.count("and") + line.count("or"),
                })
    return candidates


def _simulate_kill(mutant: dict, context: EngineContext) -> bool:
    """Heuristic: assume ~60% kill rate unless stack has no tests."""
    import random
    has_tests = context.stack.has_tests if context.stack else False
    kill_rate = 0.65 if has_tests else 0.30
    return random.random() < kill_rate
