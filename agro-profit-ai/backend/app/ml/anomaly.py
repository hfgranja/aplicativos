"""Anomaly detection (spec seção 21).

MVP substitute for the full "compare cell vs field vs own history vs
similar cells" pipeline (which needs a populated SpatialCell grid with real
multi-cell time series — Fase 2/3): an IsolationForest fitted on the same
agronomically-structured feature distribution used to bootstrap the yield
model, used as a stand-in "normal population" to score how unusual the
field's current feature vector is. Combined with a simple temporal rule
(NDVI vs 30d mean) for a second, cheap signal.
"""
from __future__ import annotations

import pandas as pd
from sklearn.ensemble import IsolationForest

from app.ml.training_data import FEATURE_COLUMNS, generate_training_frame

_FOREST_CACHE: dict[str, IsolationForest] = {}


def _get_forest(crop: str) -> IsolationForest:
    key = crop or "_default"
    if key not in _FOREST_CACHE:
        df = generate_training_frame(crop or "_default")
        forest = IsolationForest(n_estimators=150, contamination=0.08, random_state=42)
        forest.fit(df[FEATURE_COLUMNS])
        _FOREST_CACHE[key] = forest
    return _FOREST_CACHE[key]


def classify_anomaly(crop: str, feature_row: pd.DataFrame, features: dict) -> str:
    forest = _get_forest(crop)
    score = forest.decision_function(feature_row)[0]  # higher = more normal

    ndvi_current = features.get("ndvi_current")
    ndvi_mean_30d = features.get("ndvi_mean_30d")
    ndvi_drop_pct = None
    if ndvi_current is not None and ndvi_mean_30d not in (None, 0):
        ndvi_drop_pct = (ndvi_mean_30d - ndvi_current) / ndvi_mean_30d

    if score < -0.05 and ndvi_drop_pct is not None and ndvi_drop_pct > 0.20:
        return "critical"
    if score < -0.02 or (ndvi_drop_pct is not None and ndvi_drop_pct > 0.15):
        return "high"
    if score < 0.03 or (ndvi_drop_pct is not None and ndvi_drop_pct > 0.08):
        return "watch"
    return "normal"
