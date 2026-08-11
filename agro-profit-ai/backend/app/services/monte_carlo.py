"""MonteCarloEconomicSimulator (spec seção 27).

Stochastic variables: yield, commodity price, rainfall, intervention
response. Returns P5/P50/P95 margin and probability of profit / positive
intervention ROI.
"""
from __future__ import annotations

import numpy as np


def simulate(
    yield_p10_kg_ha: float,
    yield_p50_kg_ha: float,
    yield_p90_kg_ha: float,
    price_per_kg: float,
    variable_cost_per_ha: float,
    intervention_cost_per_ha: float = 0.0,
    yield_response_pct: float = 0.0,
    price_volatility_pct: float = 0.12,
    n_simulations: int = 1000,
    seed: int | None = 42,
) -> dict:
    rng = np.random.default_rng(seed)

    # Approximate the P10/P50/P90 quantile forecast as a normal distribution
    # (asymmetric spread handled by averaging the two half-widths).
    lower_spread = max(yield_p50_kg_ha - yield_p10_kg_ha, 1.0)
    upper_spread = max(yield_p90_kg_ha - yield_p50_kg_ha, 1.0)
    sigma = (lower_spread + upper_spread) / (2 * 1.2816)  # z(0.90) ≈ 1.2816

    yield_samples = rng.normal(yield_p50_kg_ha, sigma, n_simulations)
    yield_samples = np.clip(yield_samples, 0, None)

    price_samples = rng.normal(price_per_kg, price_per_kg * price_volatility_pct, n_simulations)
    price_samples = np.clip(price_samples, 0.01, None)

    response_samples = rng.normal(yield_response_pct, abs(yield_response_pct) * 0.4 + 0.01, n_simulations)
    scenario_yield_samples = yield_samples * (1 + response_samples)

    baseline_margin = yield_samples * price_samples - variable_cost_per_ha
    scenario_margin = scenario_yield_samples * price_samples - variable_cost_per_ha - intervention_cost_per_ha
    incremental_margin = scenario_margin - baseline_margin

    p5, p50, p95 = np.percentile(scenario_margin, [5, 50, 95])
    probability_of_profit = float(np.mean(scenario_margin > 0))
    probability_of_positive_roi = (
        float(np.mean(incremental_margin > 0)) if intervention_cost_per_ha else float(np.mean(incremental_margin >= 0))
    )

    return {
        "p5_margin_per_ha": round(float(p5), 2),
        "p50_margin_per_ha": round(float(p50), 2),
        "p95_margin_per_ha": round(float(p95), 2),
        "probability_of_profit": round(probability_of_profit, 3),
        "probability_of_positive_intervention_roi": round(probability_of_positive_roi, 3),
    }
