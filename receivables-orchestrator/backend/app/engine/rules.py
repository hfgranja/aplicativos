"""Motor de regras: filtra opcoes elegiveis antes do scoring (secao 3/5 do design doc).

Regras duras (nunca decididas pelo modelo de IA):
- meio explicitamente proibido pelo estabelecimento na intencao;
- meio fora da lista permitida pela politica do merchant;
- provedor indisponivel (status == "down");
- custo estimado acima do max_cost declarado;
- risco do meio acima do apetite de risco (max_risk) da intencao.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class EligibilityResult:
    method: str
    eligible: bool
    reason: Optional[str] = None


def filter_eligible_methods(
    *,
    intent_allowed: list[str],
    intent_forbidden: list[str],
    policy_allowed: list[str],
    available_methods: list[str],
) -> list[EligibilityResult]:
    results: list[EligibilityResult] = []
    allowed_base = set(available_methods)
    if intent_allowed:
        allowed_base &= set(intent_allowed)
    allowed_base &= set(policy_allowed)

    for method in available_methods:
        if method in intent_forbidden:
            results.append(EligibilityResult(method, False, "meio proibido explicitamente na intencao"))
        elif method not in allowed_base:
            results.append(EligibilityResult(method, False, "meio fora da politica do estabelecimento ou da lista permitida"))
        else:
            results.append(EligibilityResult(method, True, None))
    return results


def provider_check(provider_status: str) -> Optional[str]:
    if provider_status == "down":
        return "provedor indisponivel (circuit breaker aberto)"
    if provider_status == "degraded":
        return None  # elegivel, mas penalizado no scoring (nao é regra dura)
    return None


def cost_check(estimated_cost_pct: float, max_cost: Optional[float]) -> Optional[str]:
    if max_cost is not None and estimated_cost_pct > max_cost:
        return f"custo estimado {estimated_cost_pct:.2f}% excede max_cost declarado ({max_cost:.2f}%)"
    return None


def risk_check(method_risk: float, risk_level_exceeds: bool) -> Optional[str]:
    if risk_level_exceeds:
        return "risco do meio acima do apetite de risco (max_risk) declarado para esta intencao"
    return None
