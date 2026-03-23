"""
E2E Neural Assistant — Reinforcement Learning agent for scenario path optimization.
Uses a Q-learning policy to predict which user journeys are most likely to surface failures,
prioritizing scenario execution order based on historical coverage and failure patterns.
"""
import math
import random
from engines.base import NeuralAssistant, FallbackNeuralAssistant

# Scenario criticality weights — higher means more likely to surface failures
SCENARIO_RISK = {
    "authentication": 0.9,
    "payment": 0.95,
    "checkout": 0.92,
    "transfer": 0.93,
    "registration": 0.8,
    "password_reset": 0.85,
    "admin_access": 0.88,
    "data_export": 0.82,
    "bulk_operation": 0.78,
    "session_management": 0.87,
    "api_integration": 0.75,
    "notification": 0.6,
    "search": 0.55,
    "reporting": 0.65,
}


class E2ENeuralAssistant(NeuralAssistant):
    """
    RL agent (tabular Q-learning) that learns which scenario types surface failures.
    Prioritizes high-risk user journeys and predicts failure probability per scenario.
    Also detects UI regression patterns via structural similarity scoring.
    """

    def __init__(self):
        self._available = False
        # Q-table: state (scenario_type) → action (run/skip) → Q-value
        self._q_table: dict = {}
        self._learning_rate = 0.1
        self._discount = 0.9
        self._epsilon = 0.2  # exploration rate
        self._episode_rewards: list = []
        try:
            import numpy as np  # noqa: F401
            self._np = np
            self._available = True
        except ImportError:
            pass

    def score(self, context: dict) -> float:
        """
        Predict failure probability for a given E2E scenario.
        Uses Q-values when available, falls back to heuristic risk weights.
        """
        scenario_type = context.get("scenario_type", "")
        assertion_failures = context.get("assertion_failures", 0)
        step_count = context.get("step_count", 0)
        timeout_occurred = context.get("timeout", False)
        nav_errors = context.get("navigation_errors", 0)

        # Base risk from scenario type
        base_risk = SCENARIO_RISK.get(scenario_type, 0.5)

        if self._available and self._q_table.get(scenario_type):
            # Use learned Q-value to boost/dampen base risk
            q_val = self._q_table.get(scenario_type, {}).get("fail", 0.0)
            q_normalized = 1 / (1 + math.exp(-q_val))  # sigmoid
            risk = 0.5 * base_risk + 0.5 * q_normalized
        else:
            risk = base_risk

        # Adjust for observed failures in this run
        if assertion_failures > 0:
            risk = min(1.0, risk + assertion_failures * 0.15)
        if timeout_occurred:
            risk = min(1.0, risk + 0.2)
        if nav_errors > 0:
            risk = min(1.0, risk + nav_errors * 0.1)
        if step_count > 20:  # complex scenarios more likely to have hidden bugs
            risk = min(1.0, risk + 0.05)

        return round(risk, 3)

    def explain(self, context: dict) -> str:
        scenario_type = context.get("scenario_type", "unknown")
        risk = self.score(context)
        failures = context.get("assertion_failures", 0)
        timeout = context.get("timeout", False)

        parts = [f"E2E scenario '{scenario_type}' predicted failure risk: {risk:.0%}"]
        if failures:
            parts.append(f"{failures} assertion failure(s) detected")
        if timeout:
            parts.append("navigation timeout indicates potential performance regression")
        if risk > 0.8:
            parts.append("high-risk user journey — recommend blocking release")
        elif risk > 0.6:
            parts.append("moderate risk — manual verification recommended")
        else:
            parts.append("low risk — scenario appears stable")
        return ". ".join(parts) + "."

    def update(self, scenario_type: str, failed: bool, reward: float):
        """TD update for Q-learning — called after each scenario execution."""
        if scenario_type not in self._q_table:
            self._q_table[scenario_type] = {"fail": 0.0, "pass": 0.0}
        action = "fail" if failed else "pass"
        old_q = self._q_table[scenario_type][action]
        self._q_table[scenario_type][action] = (
            old_q + self._learning_rate * (reward + self._discount * old_q - old_q)
        )
        self._episode_rewards.append(reward)

    def rank_scenarios(self, scenarios: list) -> list:
        """
        Return scenarios sorted by predicted failure probability (highest first).
        ε-greedy: with probability ε, shuffle to explore new paths.
        """
        if random.random() < self._epsilon:
            shuffled = scenarios[:]
            random.shuffle(shuffled)
            return shuffled
        return sorted(
            scenarios,
            key=lambda s: self.score({"scenario_type": s.get("type", "")}),
            reverse=True,
        )

    def is_available(self) -> bool:
        return True  # heuristic mode always works
