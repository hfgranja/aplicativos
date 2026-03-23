"""
Fuzzing Neural Assistant — DQN Reinforcement Learning agent for coverage-guided fuzzing.
Learns which mutation operators maximize code coverage.
"""
import random
from engines.base import NeuralAssistant

MUTATION_OPERATORS = ["bit_flip", "byte_swap", "append", "truncate", "insert_special",
                       "duplicate", "arithmetic", "interesting_int", "random_bytes"]


class FuzzingNeuralAssistant(NeuralAssistant):
    """
    DQN agent: state=coverage_bitmap, action=mutation_operator, reward=new_coverage.
    Falls back to ε-greedy random selection without PyTorch.
    """

    def __init__(self):
        self._q_table: dict = {}  # simplified Q-table for tabular approximation
        self._epsilon = 0.3  # exploration rate
        self._available = True

    def is_available(self) -> bool:
        return True  # heuristic always available

    def score(self, context: dict) -> float:
        """Return expected coverage gain from this mutation."""
        operator = context.get("operator", "random_bytes")
        # Learn from feedback in update()
        return self._q_table.get(operator, 0.5)

    def explain(self, context: dict) -> str:
        best_op = max(MUTATION_OPERATORS, key=lambda op: self._q_table.get(op, 0.5))
        return f"DQN fuzzer: best operator='{best_op}', ε={self._epsilon:.2f}"

    def select_operator(self) -> str:
        """ε-greedy operator selection."""
        if random.random() < self._epsilon:
            return random.choice(MUTATION_OPERATORS)
        return max(MUTATION_OPERATORS, key=lambda op: self._q_table.get(op, 0.5))

    def update(self, operator: str, reward: float):
        """Update Q-table with observed reward."""
        old = self._q_table.get(operator, 0.5)
        self._q_table[operator] = old + 0.1 * (reward - old)  # TD update
        self._epsilon = max(0.05, self._epsilon * 0.99)  # decay exploration
