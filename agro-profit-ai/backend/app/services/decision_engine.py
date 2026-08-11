"""Decision Engine (spec seção 24) — the core product differentiator.

ML predicts. The Decision Engine decides. It takes the yield prediction,
feature-derived risk signals, soil/weather context, commodity price and a
catalog of candidate interventions, prices each one through the Economic
Engine + Monte Carlo simulator, and ranks them by Expected Economic Value
— not by potential yield increase (spec seção 2).

Risk-signal detection here is rule-based (thresholds over engineered
features): this is deliberate for the MVP — a LightGBMClassifier risk model
(spec seção 22) needs labeled crop-failure/yield-loss outcomes we don't yet
have. The rule thresholds are the hook point that model will replace
without touching the ranking/economics logic below.
"""
from __future__ import annotations

from dataclasses import dataclass, field as dc_field

from app.services import economic_engine, monte_carlo

# (response_pct, cost_per_ha) — agronomic priors, editable per crop/region as
# real outcome data accumulates (spec seção 64: MarginPredictionModel).
INTERVENTION_CATALOG = {
    "liming": {"response_pct": 0.08, "cost_per_ha": 350.0, "label": "Calagem para correção de pH"},
    "fertilization_topdress": {"response_pct": 0.05, "cost_per_ha": 280.0, "label": "Adubação de cobertura"},
    "supplemental_irrigation": {"response_pct": 0.12, "cost_per_ha": 450.0, "label": "Irrigação suplementar"},
    "pest_scouting": {"response_pct": 0.0, "cost_per_ha": 25.0, "label": "Monitoramento fitossanitário em campo"},
}


@dataclass
class RiskSignal:
    issue: str
    evidence: list[str]
    intervention_key: str
    priority: str = "medium"


def detect_risk_signals(features: dict) -> list[RiskSignal]:
    signals: list[RiskSignal] = []

    soil_ph = features.get("soil_ph")
    if soil_ph is not None and soil_ph < 5.2:
        signals.append(
            RiskSignal(
                issue="pH do solo abaixo do ideal para a cultura",
                evidence=[f"pH medido/estimado: {soil_ph}", "Faixa recomendada: 5.5–6.5"],
                intervention_key="liming",
                priority="high" if soil_ph < 4.8 else "medium",
            )
        )

    om = features.get("soil_organic_matter")
    ndvi_current = features.get("ndvi_current")
    ndvi_mean_30d = features.get("ndvi_mean_30d")
    if ndvi_current is not None and ndvi_mean_30d is not None and ndvi_current < ndvi_mean_30d * 0.85:
        signals.append(
            RiskSignal(
                issue="Queda de vigor vegetativo (NDVI) em relação à média recente",
                evidence=[
                    f"NDVI atual: {ndvi_current}",
                    f"Média 30 dias: {round(ndvi_mean_30d, 3)}",
                ],
                intervention_key="fertilization_topdress",
                priority="high",
            )
        )
    elif om is not None and om < 15:
        signals.append(
            RiskSignal(
                issue="Baixa matéria orgânica / fertilidade do solo",
                evidence=[f"Matéria orgânica: {om} g/kg"],
                intervention_key="fertilization_topdress",
                priority="medium",
            )
        )

    dry_days = features.get("consecutive_dry_days")
    water_balance = features.get("water_balance_30d")
    if (dry_days is not None and dry_days >= 10) or (water_balance is not None and water_balance < -80):
        signals.append(
            RiskSignal(
                issue="Déficit hídrico relevante no período recente",
                evidence=[
                    f"Dias consecutivos sem chuva: {dry_days}",
                    f"Balanço hídrico 30d: {water_balance} mm",
                ],
                intervention_key="supplemental_irrigation",
                priority="high",
            )
        )

    ndvi_std = features.get("ndvi_std_30d")
    if ndvi_std is not None and ndvi_std > 0.08:
        signals.append(
            RiskSignal(
                issue="Variabilidade espacial/temporal elevada de NDVI — possível estresse localizado ou praga/doença",
                evidence=[f"Desvio padrão NDVI 30d: {ndvi_std}"],
                intervention_key="pest_scouting",
                priority="low",
            )
        )

    return signals


def _classify(expected_roi: float | None, probability_positive_roi: float, confidence: float) -> str:
    if expected_roi is None:
        return "MONITOR"
    if confidence < 30:
        return "MONITOR"
    if expected_roi >= 1.0 and probability_positive_roi >= 0.6:
        return "ACTION"
    if expected_roi < 0 or probability_positive_roi < 0.35:
        return "DO_NOT_ACT"
    return "MONITOR"


def generate_recommendations(
    features: dict,
    yield_expected: float,
    yield_p10: float,
    yield_p90: float,
    price_per_kg: float,
    variable_cost_per_ha: float,
    confidence: float,
    model_version: str,
) -> list[dict]:
    """Returns recommendation dicts ranked by expected economic value
    (expected_margin_delta_per_ha), highest first."""
    baseline_margin = economic_engine.contribution_margin_per_ha(yield_expected, price_per_kg, variable_cost_per_ha)

    signals = detect_risk_signals(features)
    recommendations = []
    for signal in signals:
        intervention = INTERVENTION_CATALOG[signal.intervention_key]
        response_pct = intervention["response_pct"]
        cost = intervention["cost_per_ha"]

        scenario_yield = yield_expected * (1 + response_pct)
        scenario_margin = economic_engine.contribution_margin_per_ha(scenario_yield, price_per_kg, variable_cost_per_ha + cost)
        incremental_margin = economic_engine.incremental_margin_per_ha(scenario_margin, baseline_margin)
        expected_roi = economic_engine.roi(incremental_margin, cost)

        mc = monte_carlo.simulate(
            yield_p10_kg_ha=yield_p10,
            yield_p50_kg_ha=yield_expected,
            yield_p90_kg_ha=yield_p90,
            price_per_kg=price_per_kg,
            variable_cost_per_ha=variable_cost_per_ha,
            intervention_cost_per_ha=cost,
            yield_response_pct=response_pct,
        )

        decision = _classify(expected_roi, mc["probability_of_positive_intervention_roi"], confidence)

        recommendations.append(
            {
                "priority": signal.priority,
                "issue": signal.issue,
                "evidence": signal.evidence,
                "suggested_action": intervention["label"],
                "estimated_cost_per_ha": cost,
                "expected_yield_delta_kg_ha": round(scenario_yield - yield_expected, 1),
                "expected_margin_delta_per_ha": incremental_margin,
                "expected_roi": expected_roi if expected_roi is not None else 0.0,
                "confidence": confidence,
                "decision": decision,
                "model_version": model_version,
                "monte_carlo": mc,
            }
        )

    recommendations.sort(key=lambda r: r["expected_margin_delta_per_ha"], reverse=True)
    return recommendations
