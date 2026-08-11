"""Decision Engine (spec seção 24) — o principal diferencial do produto.

O ML prevê. O motor agronômico diagnostica e prescreve (dose, lâmina,
janela). O Decision Engine precifica cada intervenção candidata via
Economic Engine + Monte Carlo e ordena por VALOR ECONÔMICO ESPERADO
(margem incremental por hectare), classificando cada uma como
ACTION / MONITOR / DO_NOT_ACT — nunca apenas pelo potencial de aumento de
produção (spec seção 2).

As regras agronômicas com dose calculada vivem em
services/agronomy_engine.py; este módulo permanece agnóstico ao conteúdo
técnico das intervenções, cuidando só de economia, risco e priorização —
o hook onde um futuro LightGBMClassifier de risco / MarginPredictionModel
(spec seções 22 e 64) substitui as heurísticas sem tocar o ranking.
"""
from __future__ import annotations

from app.services import economic_engine, monte_carlo
from app.services.agronomy_engine import AgronomicAction


def _classify(expected_roi: float | None, probability_positive_roi: float, confidence: float, cost: float) -> str:
    if cost <= 0:
        # Ações sem custo direto (ex.: planejamento de janela de plantio)
        return "ACTION" if confidence >= 30 else "MONITOR"
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
    agronomic_actions: list[AgronomicAction],
    yield_expected: float,
    yield_p10: float,
    yield_p90: float,
    price_per_kg: float,
    variable_cost_per_ha: float,
    confidence: float,
    model_version: str,
) -> list[dict]:
    """Precifica e ranqueia as ações do motor agronômico por margem
    incremental esperada por hectare (maior primeiro)."""
    baseline_margin = economic_engine.contribution_margin_per_ha(yield_expected, price_per_kg, variable_cost_per_ha)

    recommendations = []
    for action in agronomic_actions:
        cost = action.cost_per_ha
        response_pct = action.response_pct

        scenario_yield = yield_expected * (1 + response_pct)
        scenario_margin = economic_engine.contribution_margin_per_ha(
            scenario_yield, price_per_kg, variable_cost_per_ha + cost
        )
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

        decision = _classify(expected_roi, mc["probability_of_positive_intervention_roi"], confidence, cost)

        evidence = list(action.evidence)
        if action.dose_description:
            evidence.append(f"Prescrição: {action.dose_description}")

        recommendations.append(
            {
                "category": action.category,
                "priority": action.priority,
                "issue": action.issue,
                "evidence": evidence,
                "suggested_action": action.action_label,
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
