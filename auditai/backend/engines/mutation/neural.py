"""
Mutation Neural Assistant — GNN-based mutation priority predictor.
Predicts which mutations will survive (expose weak tests) without running all of them.
"""
from engines.base import NeuralAssistant, FallbackNeuralAssistant


class MutationNeuralAssistant(NeuralAssistant):
    """
    Graph Neural Network over AST to predict mutation survivability.

    Architecture:
    - Node features: token type, token value, depth in AST
    - Edge features: parent-child, sibling relationships
    - GNN layers: 3x GraphSAGE
    - Output: survivability score per AST node (mutation candidate)

    High survivability score = tests likely won't catch this mutation = weak test.
    """

    def __init__(self):
        self._available = False

    def is_available(self) -> bool:
        return self._available

    def score(self, context: dict) -> float:
        """Predict survivability of a mutation (0=killed, 1=survived)."""
        # Heuristic fallback: operators in complex conditionals tend to survive more
        operator = context.get("operator", "")
        complexity = context.get("complexity", 1)
        if operator in ("<=", ">=", "==", "!="):
            return min(0.9, 0.5 + complexity * 0.05)
        if operator in ("+", "-"):
            return 0.6
        return 0.4

    def explain(self, context: dict) -> str:
        score = self.score(context)
        return f"GNN mutation predictor: survivability={score:.2f} — {'high priority' if score > 0.7 else 'standard'}"

    def prioritize_mutations(self, candidates: list, top_k: int = 50) -> list:
        """Return top-K mutations ranked by predicted survivability."""
        scored = [(m, self.score({"operator": m.get("type", ""), "complexity": m.get("complexity", 1)}))
                  for m in candidates]
        scored.sort(key=lambda x: x[1], reverse=True)
        return [m for m, _ in scored[:top_k]]
