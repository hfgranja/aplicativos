"""YieldModel (spec seções 16-20) — orchestrates champion prediction,
P10/P50/P90 quantiles, farm-history calibration, SHAP explanation and
anomaly classification into a single prediction payload.
"""
from __future__ import annotations

import pandas as pd

from app.ml import anomaly, explainability
from app.ml.model_registry import get_or_train_crop_model
from app.ml.training_data import FEATURE_COLUMNS, generate_training_frame


def _feature_row(crop: str, features: dict) -> pd.DataFrame:
    """Builds the model input row, filling any feature we couldn't compute
    for this field (missing weather/soil/satellite data) with the crop's
    synthetic-prior median — keeps inference robust under partial data
    while the Confidence Engine separately penalizes the gaps."""
    reference = generate_training_frame(crop or "_default")
    row = {}
    for col in FEATURE_COLUMNS:
        value = features.get(col)
        row[col] = value if value is not None else float(reference[col].median())
    return pd.DataFrame([row], columns=FEATURE_COLUMNS)


def _calibrate_with_history(model_p50: float, features: dict) -> float:
    """Shrinks the global-model prediction toward the field's own realized
    yield history, when available — a lightweight bridge toward the
    farm-personalized models planned for Fase 3 (spec seção 43 hierarchy:
    farm -> regional -> global fallback)."""
    n_seasons = features.get("historical_seasons_count") or 0
    historical_mean = features.get("historical_yield_mean_kg_ha")
    if not n_seasons or historical_mean is None:
        return model_p50
    weight_history = min(0.7, 0.25 * n_seasons)
    return round(model_p50 * (1 - weight_history) + historical_mean * weight_history, 1)


def predict_yield(crop: str, features: dict) -> dict:
    trained = get_or_train_crop_model(crop)
    row = _feature_row(crop, features)

    p10 = float(trained.quantile_models[0.1].predict(row)[0])
    p50_raw = float(trained.quantile_models[0.5].predict(row)[0])
    p90 = float(trained.quantile_models[0.9].predict(row)[0])
    p10, p90 = min(p10, p90), max(p10, p90)

    p50 = _calibrate_with_history(p50_raw, features)
    # Keep the calibrated expected value inside the uncalibrated [p10, p90]
    # band width, re-centering the band around it.
    half_width = max((p90 - p10) / 2, 1.0)
    p10, p90 = round(p50 - half_width, 1), round(p50 + half_width, 1)

    shap_explanation = explainability.explain_prediction(trained.champion_model, row)
    risk_level = anomaly.classify_anomaly(crop, row, features)

    return {
        "model_id": f"yield-{trained.champion_name}",
        "model_version": trained.version,
        "champion_name": trained.champion_name,
        "challenger_name": trained.challenger_name,
        "champion_mae_kg_ha": trained.champion_mae,
        "challenger_mae_kg_ha": trained.challenger_mae,
        "yield_expected_kg_ha": round(p50, 1),
        "yield_p10_kg_ha": p10,
        "yield_p90_kg_ha": p90,
        "risk_level": risk_level,
        "shap_explanation": shap_explanation,
        "feature_values": {k: v for k, v in features.items() if not k.startswith("_")},
    }
