"""Agente de Explicabilidade (secao 10 e 19 do design doc).

Gera a explicacao de uma decisao para diferentes publicos a partir do mesmo
DecisionScore — nao ha "segunda fonte da verdade", apenas linguagem
adaptada por audiencia.
"""
from __future__ import annotations

METHOD_LABEL = {
    "pix": "Pix",
    "credit_card": "cartão de crédito",
    "debit_card": "cartão de débito",
    "boleto": "boleto",
    "payment_link": "link de pagamento",
}


def _label(method: str) -> str:
    return METHOD_LABEL.get(method, method)


def build_reason_summary(chosen: dict, weights: dict) -> str:
    top_dim = max(weights, key=weights.get)
    dim_label = {
        "conversion": "conversão",
        "cost": "custo",
        "risk": "risco",
        "liquidity": "liquidez",
        "experience": "experiência",
        "preference": "preferência do cliente",
    }[top_dim]
    return (
        f"{_label(chosen['method']).capitalize()} foi recomendado por maximizar o score composto "
        f"(score={chosen['score']:.2f}, confiança={chosen['confidence']:.0%}), priorizando {dim_label} "
        f"conforme a política vigente. Conversão esperada de {chosen['estimated_conversion']:.0%}, "
        f"custo estimado de {chosen['estimated_cost_pct']:.2f}% e liquidação em "
        f"~{chosen['estimated_settlement_hours']:.0f}h."
    )


def build_discarded(all_options: list[dict], chosen_method: str) -> list[dict]:
    discarded = []
    for opt in all_options:
        if opt["method"] == chosen_method:
            continue
        if not opt["eligible"]:
            reason = opt.get("exclusion_reason") or "não elegível"
        else:
            reason = f"score inferior ({opt.get('score', 0):.2f} vs {'-'} do meio escolhido)"
        discarded.append({"method": opt["method"], "reason": reason, "score": opt.get("score")})
    return discarded


def build_audience_explanations(*, intent: dict, chosen: dict | None, discarded: list[dict], weights: dict) -> list[dict]:
    if chosen is None:
        return [{
            "audience": "geral",
            "text": "Nenhuma opção elegível foi encontrada para esta intenção dentro das regras e limites configurados.",
        }]

    method_label = _label(chosen["method"])
    top_discard = discarded[0] if discarded else None

    cfo_text = (
        f"A cobrança de R$ {intent['amount']:.2f} foi roteada via {method_label}, com custo estimado de "
        f"{chosen['estimated_cost_pct']:.2f}% e liquidação em ~{chosen['estimated_settlement_hours']:.0f}h. "
        f"Dentro do limite de custo definido pela política."
    )

    financeiro_text = (
        f"Recomendamos {method_label} para este cliente porque a conversão esperada "
        f"({chosen['estimated_conversion']:.0%}) e o prazo de liquidação superam as alternativas "
        f"consideradas, respeitando os limites de risco configurados."
    )

    atendimento_text = (
        f"O cliente recebeu cobrança via {method_label}. "
        + (f"A alternativa mais próxima ({_label(top_discard['method'])}) foi descartada: {top_discard['reason']}."
           if top_discard else "Não havia alternativas elegíveis.")
    )

    merchant_text = (
        f"Recomendamos {method_label} para esta cobrança: maior chance de receber dentro do seu objetivo "
        f"declarado, com custo dentro do limite configurado."
    )

    audit_text = (
        f"Decisão para intenção {intent['id']}: método escolhido={chosen['method']}, "
        f"score={chosen['score']:.4f}, confiança={chosen['confidence']:.4f}, "
        f"pesos aplicados={weights}. Nenhuma regra dura violada. Log completo disponível em AuditLog."
    )

    cliente_text = (
        f"Preparamos uma opção de pagamento via {method_label} para você"
        + (", rápida e sem burocracia." if chosen["method"] == "pix" else ".")
    )

    return [
        {"audience": "cfo", "text": cfo_text},
        {"audience": "financeiro", "text": financeiro_text},
        {"audience": "atendimento", "text": atendimento_text},
        {"audience": "estabelecimento", "text": merchant_text},
        {"audience": "auditoria", "text": audit_text},
        {"audience": "cliente_final", "text": cliente_text},
    ]
