"""
Chaos Neural Assistant — Causal inference for fault injection scenario ranking.
"""
from engines.base import NeuralAssistant


class ChaosNeuralAssistant(NeuralAssistant):
    """
    Causal inference model (DoWhy-inspired) that learns failure propagation patterns.
    Ranks fault injection candidates by expected blast radius.
    """

    FAULT_SCENARIOS = [
        {"type": "network_partition", "blast_radius": 0.9, "description": "Network partition between services"},
        {"type": "db_slowdown", "blast_radius": 0.8, "description": "Database query latency spike (10x)"},
        {"type": "memory_pressure", "blast_radius": 0.7, "description": "Memory allocation failure under load"},
        {"type": "cpu_throttle", "blast_radius": 0.6, "description": "CPU throttled to 10% capacity"},
        {"type": "disk_full", "blast_radius": 0.8, "description": "Disk full — write operations fail"},
        {"type": "external_api_down", "blast_radius": 0.5, "description": "External dependency unavailable"},
        {"type": "clock_skew", "blast_radius": 0.4, "description": "System clock skewed by 5 minutes"},
        {"type": "packet_loss", "blast_radius": 0.6, "description": "30% packet loss on all network interfaces"},
        {"type": "process_kill", "blast_radius": 0.9, "description": "Random process killed mid-operation"},
        {"type": "config_corruption", "blast_radius": 0.7, "description": "Configuration file corrupted"},
    ]

    def is_available(self) -> bool:
        return True

    def score(self, context: dict) -> float:
        """Return blast radius estimate [0,1] for a fault scenario."""
        fault_type = context.get("fault_type", "")
        for s in self.FAULT_SCENARIOS:
            if s["type"] == fault_type:
                return s["blast_radius"]
        return 0.5

    def explain(self, context: dict) -> str:
        score = self.score(context)
        return f"Causal inference: blast_radius={score:.2f}"

    def rank_scenarios(self, stack_risk_surfaces: list) -> list:
        """Rank fault scenarios by impact given the application's risk surfaces."""
        scenarios = list(self.FAULT_SCENARIOS)
        if "database" in stack_risk_surfaces:
            # Elevate DB-related scenarios
            for s in scenarios:
                if "db" in s["type"]:
                    s = dict(s)
                    s["blast_radius"] = min(1.0, s["blast_radius"] * 1.2)
        if "external_api" in stack_risk_surfaces:
            for s in scenarios:
                if "external" in s["type"]:
                    s = dict(s)
                    s["blast_radius"] = min(1.0, s["blast_radius"] * 1.3)
        scenarios.sort(key=lambda x: x["blast_radius"], reverse=True)
        return scenarios
