"""Análise de yield gap — quanto falta para o teto e o que está limitando.

Decompõe a distância entre a produtividade prevista e o teto atingível da
cultura (crop_knowledge) em fatores limitantes quantificados, no espírito
da lei do mínimo de Liebig: o fator mais limitante define a prioridade de
manejo. Cada fator recebe uma penalidade estimada (fração do potencial)
derivada das mesmas regras do motor agronômico, de modo que o produtor vê
"onde estão os kg/ha que faltam" e as recomendações mostram como
recuperá-los.

Camadas do gap:
- potential: teto da cultura sem limitação (irrigado, sem estresse)
- attainable: teto realista em sequeiro bem manejado
- predicted: previsão do modelo para o talhão
- regional: benchmark municipal IBGE (quando disponível) — contexto, nunca
  ground truth (spec 4.12)
"""
from __future__ import annotations

from app.domain.crop_knowledge import get_crop_knowledge


def compute_yield_gap(
    crop: str | None,
    predicted_yield_kg_ha: float,
    features: dict,
    water_balance: dict,
    phenology: dict,
    regional_benchmark_kg_ha: float | None = None,
) -> dict:
    kb = get_crop_knowledge(crop)
    attainable = kb.yield_attainable_kg_ha
    potential = kb.yield_potential_kg_ha

    limiting_factors = []

    def add_factor(name: str, label: str, penalty_pct: float, evidence: str):
        if penalty_pct <= 0.5:
            return
        limiting_factors.append(
            {
                "factor": name,
                "label": label,
                "penalty_pct": round(penalty_pct, 1),
                "recoverable_kg_ha": round(attainable * penalty_pct / 100, 0),
                "evidence": evidence,
            }
        )

    # --- Água ---
    stress = water_balance.get("water_stress_index") if water_balance.get("available") else None
    if stress is not None and stress > 10:
        in_critical = phenology.get("available") and phenology.get("current_water_sensitivity", 0) >= 0.8
        penalty = min(30.0, stress * (0.35 if in_critical else 0.20))
        add_factor(
            "water",
            "Déficit hídrico",
            penalty,
            f"Índice de estresse FAO-56: {stress}" + (" em fase crítica" if in_critical else ""),
        )

    # --- Acidez do solo ---
    v_pct = features.get("soil_base_saturation")
    if v_pct is not None and v_pct < kb.target_base_saturation_pct - 5:
        gap_v = kb.target_base_saturation_pct - v_pct
        add_factor("acidity", "Acidez do solo (V% baixo)", min(12.0, gap_v * 0.4), f"V% {v_pct:.0f} vs alvo {kb.target_base_saturation_pct:.0f}%")
    else:
        ph = features.get("soil_ph")
        if ph is not None and ph < kb.ph_ideal[0] - 0.3:
            add_factor("acidity", "Acidez do solo (pH baixo)", 6.0, f"pH {ph} vs faixa {kb.ph_ideal[0]}-{kb.ph_ideal[1]}")

    # --- Fertilidade P/K ---
    p = features.get("soil_phosphorus")
    if p is not None and p < kb.p_critical_mg_dm3:
        deficit_ratio = (kb.p_critical_mg_dm3 - p) / kb.p_critical_mg_dm3
        add_factor("phosphorus", "Fósforo abaixo do crítico", min(10.0, deficit_ratio * 12), f"P {p} vs crítico {kb.p_critical_mg_dm3} mg/dm³")
    k = features.get("soil_potassium")
    if k is not None and k < kb.k_critical_cmolc_dm3:
        add_factor("potassium", "Potássio abaixo do crítico", 5.0, f"K {k} vs crítico {kb.k_critical_cmolc_dm3} cmolc/dm³")

    # --- Estresse térmico em fase crítica ---
    heat_days = phenology.get("critical_stage_heat_days", 0) if phenology.get("available") else 0
    if heat_days >= 3:
        add_factor("heat", "Calor extremo em fase crítica", min(8.0, heat_days * 1.5), f"{heat_days} dias ≥ {kb.heat_stress_c}°C em fase sensível")

    # --- Vigor vegetativo ---
    ndvi_current = features.get("ndvi_current")
    ndvi_mean = features.get("ndvi_mean_30d")
    if ndvi_current is not None and ndvi_mean not in (None, 0):
        drop = (ndvi_mean - ndvi_current) / ndvi_mean
        if drop > 0.12:
            add_factor("vigor", "Queda de vigor vegetativo (NDVI)", min(10.0, drop * 40), f"NDVI caiu {drop * 100:.0f}% vs média 30d")

    limiting_factors.sort(key=lambda f: f["penalty_pct"], reverse=True)

    gap_to_attainable = max(0.0, attainable - predicted_yield_kg_ha)
    explained = sum(f["recoverable_kg_ha"] for f in limiting_factors)

    return {
        "crop": kb.crop,
        "crop_label": kb.label_pt,
        "yield_potential_kg_ha": potential,
        "yield_attainable_kg_ha": attainable,
        "yield_predicted_kg_ha": round(predicted_yield_kg_ha, 0),
        "yield_regional_kg_ha": round(regional_benchmark_kg_ha, 0) if regional_benchmark_kg_ha else None,
        "gap_to_attainable_kg_ha": round(gap_to_attainable, 0),
        "gap_explained_kg_ha": round(min(explained, gap_to_attainable), 0),
        "gap_pct_of_attainable": round(gap_to_attainable / attainable * 100, 1) if attainable else 0,
        "limiting_factors": limiting_factors,
        "most_limiting": limiting_factors[0]["label"] if limiting_factors else None,
    }
