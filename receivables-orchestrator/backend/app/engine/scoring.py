"""Motor de decisao / scoring (secao 5 do design doc).

Score(o) = w_conv  * conversao_esperada(o)
         + w_custo * (1 - custo_normalizado(o))
         + w_risco * (1 - risco_normalizado(o))
         + w_liq   * liquidez_normalizada(o)
         + w_exp   * experiencia_esperada(o)
         + w_pref  * aderencia_preferencia(o)

Custo e risco entram como "1 - normalizado" para que todos os termos sejam
scores em [0,1] onde "maior e melhor" — isso é matematicamente equivalente à
formula com sinais de subtracao do documento de design (pesos positivos
aplicados a (1 - dimensao)), mas facilita normalizacao e explicabilidade.
"""
from __future__ import annotations

from dataclasses import dataclass

MAX_REASONABLE_COST_PCT = 10.0
MAX_REASONABLE_SETTLEMENT_HOURS = 96.0  # 4 dias como teto de normalizacao

BASE_EXPERIENCE = {
    "pix": 0.92,
    "credit_card": 0.80,
    "debit_card": 0.78,
    "boleto": 0.55,
    "payment_link": 0.72,
}


@dataclass
class OptionEstimate:
    method: str
    provider_id: str | None
    provider_name: str | None
    estimated_cost_pct: float
    estimated_conversion: float
    estimated_settlement_hours: float
    estimated_risk: float
    estimated_experience: float
    preference_match: float


@dataclass
class ScoredOption:
    estimate: OptionEstimate
    score: float
    confidence: float
    breakdown: dict


def estimate_option(
    *,
    method: str,
    provider_id: str | None,
    provider_name: str | None,
    base_cost_pct: float,
    fixed_fee: float,
    amount: float,
    base_conversion: float,
    provider_status: str,
    avg_settlement_hours: float,
    method_risk: float,
    preferred_method: str | None,
    historical_payment_method: str | None,
    liquidity_need: str,
) -> OptionEstimate:
    cost_pct = base_cost_pct + (fixed_fee / amount * 100 if amount else 0)

    conversion = base_conversion
    if provider_status == "degraded":
        conversion *= 0.85
    if preferred_method == method:
        conversion = min(conversion + 0.06, 0.99)
    if historical_payment_method == method:
        conversion = min(conversion + 0.03, 0.99)

    settlement_hours = avg_settlement_hours
    if liquidity_need == "urgent" and method == "boleto":
        # boleto so liquida apos compensacao bancaria — pior ainda sob urgencia
        settlement_hours *= 1.1

    experience = BASE_EXPERIENCE.get(method, 0.65)
    if preferred_method == method:
        experience = min(experience + 0.08, 1.0)

    preference_match = 0.35
    if preferred_method == method:
        preference_match = 1.0
    elif historical_payment_method == method:
        preference_match = 0.7

    return OptionEstimate(
        method=method,
        provider_id=provider_id,
        provider_name=provider_name,
        estimated_cost_pct=round(cost_pct, 3),
        estimated_conversion=round(min(conversion, 0.99), 3),
        estimated_settlement_hours=round(settlement_hours, 1),
        estimated_risk=round(method_risk, 3),
        estimated_experience=round(experience, 3),
        preference_match=round(preference_match, 3),
    )


def score_option(estimate: OptionEstimate, weights: dict, data_completeness: float) -> ScoredOption:
    cost_norm = min(estimate.estimated_cost_pct / MAX_REASONABLE_COST_PCT, 1.0)
    liquidity_norm = 1 - min(estimate.estimated_settlement_hours / MAX_REASONABLE_SETTLEMENT_HOURS, 1.0)
    risk_norm = estimate.estimated_risk

    conv_term = weights["conversion"] * estimate.estimated_conversion
    cost_term = weights["cost"] * (1 - cost_norm)
    risk_term = weights["risk"] * (1 - risk_norm)
    liq_term = weights["liquidity"] * liquidity_norm
    exp_term = weights["experience"] * estimate.estimated_experience
    pref_term = weights["preference"] * estimate.preference_match

    raw_score = conv_term + cost_term + risk_term + liq_term + exp_term + pref_term
    weight_sum = sum(weights.values()) or 1.0
    score = round(raw_score / weight_sum, 4)

    # Confianca: maior quando ha historico do cliente, provedor saudavel e
    # o score nao esta em zona de empate tecnico entre risco e conversao.
    confidence = 0.55
    confidence += 0.20 * data_completeness
    confidence += 0.10 if estimate.estimated_risk < 0.4 else -0.05
    confidence += 0.05 if estimate.estimated_conversion > 0.75 else 0.0
    confidence = round(max(0.05, min(confidence, 0.99)), 3)

    breakdown = {
        "conversion_term": round(conv_term, 4),
        "cost_term": round(cost_term, 4),
        "risk_term": round(risk_term, 4),
        "liquidity_term": round(liq_term, 4),
        "experience_term": round(exp_term, 4),
        "preference_term": round(pref_term, 4),
        "cost_normalized": round(cost_norm, 4),
        "liquidity_normalized": round(liquidity_norm, 4),
        "risk_normalized": round(risk_norm, 4),
    }

    return ScoredOption(estimate=estimate, score=score, confidence=confidence, breakdown=breakdown)


def rank_options(scored: list[ScoredOption]) -> list[ScoredOption]:
    return sorted(scored, key=lambda s: s.score, reverse=True)


DEFAULT_WEIGHTS_BY_OBJECTIVE = {
    "maximize_conversion": {"conversion": 0.40, "cost": 0.10, "risk": 0.15, "liquidity": 0.10, "experience": 0.15, "preference": 0.10},
    "minimize_cost": {"conversion": 0.15, "cost": 0.45, "risk": 0.15, "liquidity": 0.10, "experience": 0.05, "preference": 0.10},
    "minimize_risk": {"conversion": 0.15, "cost": 0.10, "risk": 0.45, "liquidity": 0.10, "experience": 0.10, "preference": 0.10},
    "maximize_liquidity": {"conversion": 0.15, "cost": 0.10, "risk": 0.15, "liquidity": 0.45, "experience": 0.05, "preference": 0.10},
    "maximize_experience": {"conversion": 0.15, "cost": 0.10, "risk": 0.10, "liquidity": 0.10, "experience": 0.45, "preference": 0.10},
    "balanced": {"conversion": 0.22, "cost": 0.22, "risk": 0.22, "liquidity": 0.14, "experience": 0.12, "preference": 0.08},
}

# Piso duro: mesmo em "maximize_conversion", o peso de risco nunca cai
# abaixo deste valor — guardrail de negocio (secao 5 do design doc).
RISK_WEIGHT_FLOOR = 0.10


def resolve_weights(objective: str, custom_weights: dict | None) -> dict:
    weights = dict(DEFAULT_WEIGHTS_BY_OBJECTIVE.get(objective, DEFAULT_WEIGHTS_BY_OBJECTIVE["balanced"]))
    if custom_weights:
        weights.update({k: v for k, v in custom_weights.items() if k in weights and v is not None})
    if weights["risk"] < RISK_WEIGHT_FLOOR:
        weights["risk"] = RISK_WEIGHT_FLOOR
    return weights
