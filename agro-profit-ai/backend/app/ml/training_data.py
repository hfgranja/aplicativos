"""Bootstrap "Global Crop Model" training frame.

We do not yet have a real multi-farm, multi-season proprietary dataset —
that dataset (soil + weather + satellite + management + realized yield +
cost + price) is precisely the long-term moat described in the product
strategy (spec seção 64) and only accumulates after tenants use the
product for real seasons.

Until then, Phase 1 needs a working, honestly-labeled LightGBM/XGBoost
champion-vs-challenger pipeline end to end (spec seção 59). This module
generates a literature-informed synthetic training frame per crop: base
national-average yields are anchored to IBGE PAM order-of-magnitude
figures, and features are combined through a documented agronomic
response function (rainfall adequacy, thermal accumulation, vegetation
vigor, soil fertility/pH, water stress) plus noise.

This is a *prior*, not a fitted model on real outcomes — every prediction
made from it is capped at LOW/MEDIUM confidence by the Confidence Engine
until the tenant's own YieldRecord history grows (see yield_model.py
`_calibrate_with_history`). It exists to be replaced by real regional/farm
models as data accumulates (spec seção 43 model hierarchy), not to be
mistaken for one.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

FEATURE_COLUMNS = [
    "rain_30d",
    "rain_90d",
    "temperature_mean_30d",
    "growing_degree_days_90d",
    "consecutive_dry_days",
    "ndvi_current",
    "ndvi_mean_30d",
    "soil_ph",
    "soil_organic_matter",
    "soil_clay",
    "soil_cec",
    "fertilizer_cost_per_ha",
]

# Approximate national-average yield anchors (kg/ha), order of magnitude
# from IBGE PAM historical series — used only to center the synthetic prior.
CROP_BASE_YIELD_KG_HA = {
    "soja": 3300,
    "milho": 5600,
    "algodao": 1700,
    "cafe": 1500,
    "cana_de_acucar": 75000,
    "feijao": 1100,
    "trigo": 2900,
}
DEFAULT_BASE_YIELD = 3000


def _feature_ranges(crop: str) -> dict[str, tuple[float, float]]:
    return {
        "rain_30d": (10, 220),
        "rain_90d": (60, 650),
        "temperature_mean_30d": (17, 30),
        "growing_degree_days_90d": (400, 1400),
        "consecutive_dry_days": (0, 25),
        "ndvi_current": (0.25, 0.90),
        "ndvi_mean_30d": (0.25, 0.90),
        "soil_ph": (4.3, 6.8),
        "soil_organic_matter": (8, 45),
        "soil_clay": (10, 65),
        "soil_cec": (3, 16),
        "fertilizer_cost_per_ha": (0, 900),
    }


def generate_training_frame(crop: str, n_rows: int = 2000, seed: int = 7) -> pd.DataFrame:
    rng = np.random.default_rng(seed + abs(hash(crop)) % 1000)
    ranges = _feature_ranges(crop)
    base_yield = CROP_BASE_YIELD_KG_HA.get(crop, DEFAULT_BASE_YIELD)

    data = {col: rng.uniform(lo, hi, n_rows) for col, (lo, hi) in ranges.items()}
    df = pd.DataFrame(data)

    # Agronomic response function — each factor is a multiplier around 1.0.
    rain_adequacy = 1 - np.clip(np.abs(df["rain_90d"] - base_yield / 10) / (base_yield / 5), 0, 0.35)
    thermal = 1 - np.clip(np.abs(df["growing_degree_days_90d"] - 900) / 3000, 0, 0.25)
    vigor = 0.65 + 0.55 * df["ndvi_mean_30d"]
    ph_factor = 1 - np.clip(np.abs(df["soil_ph"] - 6.0) * 0.10, 0, 0.30)
    fertility = 0.85 + 0.15 * np.clip(df["soil_organic_matter"] / 30, 0, 1.3)
    drought_penalty = 1 - np.clip(df["consecutive_dry_days"] / 40, 0, 0.35)
    fertilization_boost = 1 + np.clip(df["fertilizer_cost_per_ha"] / 3000, 0, 0.12)

    multiplier = rain_adequacy * thermal * vigor * ph_factor * fertility * drought_penalty * fertilization_boost
    noise = rng.normal(1.0, 0.06, n_rows)
    df["yield_kg_ha"] = np.clip(base_yield * multiplier * noise, base_yield * 0.15, base_yield * 1.6)

    return df
