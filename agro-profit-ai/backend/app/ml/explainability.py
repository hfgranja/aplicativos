"""Explainability via SHAP (spec seção 23).

Never present a recommendation without the factors that drove it. Feature
keys are translated to short PT-BR labels matching the spec's example
format ("NDVI +420 kg/ha", "chuva últimos 30 dias -310 kg/ha", ...).
"""
from __future__ import annotations

import pandas as pd
import shap

FEATURE_LABELS = {
    "rain_30d": "chuva últimos 30 dias",
    "rain_90d": "chuva últimos 90 dias",
    "temperature_mean_30d": "temperatura média 30 dias",
    "growing_degree_days_90d": "graus-dia acumulados (90d)",
    "consecutive_dry_days": "dias consecutivos sem chuva",
    "ndvi_current": "NDVI atual",
    "ndvi_mean_30d": "NDVI médio 30 dias",
    "soil_ph": "pH do solo",
    "soil_organic_matter": "matéria orgânica do solo",
    "soil_clay": "teor de argila",
    "soil_cec": "CTC do solo",
    "fertilizer_cost_per_ha": "investimento em adubação",
}


def explain_prediction(model, feature_row: pd.DataFrame, top_n: int = 6) -> list[dict]:
    explainer = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(feature_row)
    if hasattr(shap_values, "ndim") and shap_values.ndim > 1:
        shap_values = shap_values[0]

    contributions = list(zip(feature_row.columns, shap_values))
    contributions.sort(key=lambda c: abs(c[1]), reverse=True)

    return [
        {
            "feature": feature,
            "label": FEATURE_LABELS.get(feature, feature),
            "contribution_kg_ha": round(float(value), 1),
        }
        for feature, value in contributions[:top_n]
    ]
