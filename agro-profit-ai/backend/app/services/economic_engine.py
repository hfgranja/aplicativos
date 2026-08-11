"""Economic Engine (spec seção 26).

Pure functions turning yield + price + cost into margin/ROI/break-even —
the core KPI of the product is Expected Contribution Margin per Hectare,
not yield alone (spec seção 2).
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class MarginResult:
    gross_revenue_per_ha: float
    contribution_margin_per_ha: float


def gross_revenue_per_ha(yield_kg_ha: float, price_per_kg: float) -> float:
    return round(yield_kg_ha * price_per_kg, 2)


def contribution_margin_per_ha(yield_kg_ha: float, price_per_kg: float, variable_cost_per_ha: float) -> float:
    return round(gross_revenue_per_ha(yield_kg_ha, price_per_kg) - variable_cost_per_ha, 2)


def incremental_margin_per_ha(scenario_margin_per_ha: float, baseline_margin_per_ha: float) -> float:
    return round(scenario_margin_per_ha - baseline_margin_per_ha, 2)


def roi(incremental_margin_per_ha_value: float, intervention_cost_per_ha: float) -> float | None:
    if not intervention_cost_per_ha:
        return None
    return round(incremental_margin_per_ha_value / intervention_cost_per_ha, 3)


def break_even_price(variable_cost_per_ha: float, yield_kg_ha: float) -> float:
    if not yield_kg_ha:
        return float("inf")
    return round(variable_cost_per_ha / yield_kg_ha, 4)


def break_even_yield(variable_cost_per_ha: float, price_per_kg: float) -> float:
    if not price_per_kg:
        return float("inf")
    return round(variable_cost_per_ha / price_per_kg, 1)


def expected_value(outcomes: list[tuple[float, float]]) -> float:
    """outcomes: list of (probability, value)."""
    return round(sum(p * v for p, v in outcomes), 2)


def downside_risk(p10_margin_per_ha: float, expected_margin_per_ha: float) -> float:
    """Expected shortfall proxy: how far the pessimistic (P10) outcome sits
    below the expected margin — the number a risk-averse producer cares
    about more than the mean."""
    return round(expected_margin_per_ha - p10_margin_per_ha, 2)
