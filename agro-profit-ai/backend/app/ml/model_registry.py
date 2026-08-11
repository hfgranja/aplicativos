"""Minimal in-process Model Registry (spec seções 17-18, 42-43).

Trains Champion (LightGBM) vs Challenger (XGBoost) on a temporal/random
holdout, picks the lower-MAE model as champion, and caches the fitted
pair per crop so repeated predictions don't retrain on every request. A
production deployment replaces this cache with MLflow (dataset version,
feature version, params, metrics, alias champion/challenger/deprecated —
see docs/DESIGN.md "MLOps").
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

import lightgbm as lgb
import numpy as np
import xgboost as xgb
from sklearn.metrics import mean_absolute_error
from sklearn.model_selection import train_test_split

from app.ml.training_data import FEATURE_COLUMNS, generate_training_frame


@dataclass
class TrainedCropModel:
    crop: str
    champion_name: str
    champion_model: object
    quantile_models: dict  # {0.1: model, 0.5: model, 0.9: model}
    challenger_name: str
    challenger_mae: float
    champion_mae: float
    trained_at: str
    version: str
    feature_columns: list


_REGISTRY: dict[str, TrainedCropModel] = {}


def _train_lightgbm(X_train, y_train):
    model = lgb.LGBMRegressor(
        n_estimators=250, max_depth=6, learning_rate=0.05, subsample=0.8, colsample_bytree=0.8, verbose=-1
    )
    model.fit(X_train, y_train)
    return model


def _train_xgboost(X_train, y_train):
    model = xgb.XGBRegressor(
        n_estimators=250, max_depth=6, learning_rate=0.05, subsample=0.8, colsample_bytree=0.8, verbosity=0
    )
    model.fit(X_train, y_train)
    return model


def _train_quantile_lightgbm(X_train, y_train, alpha: float):
    model = lgb.LGBMRegressor(
        objective="quantile", alpha=alpha, n_estimators=200, max_depth=5, learning_rate=0.05, verbose=-1
    )
    model.fit(X_train, y_train)
    return model


def get_or_train_crop_model(crop: str) -> TrainedCropModel:
    key = crop or "_default"
    if key in _REGISTRY:
        return _REGISTRY[key]

    df = generate_training_frame(crop or "_default")
    X = df[FEATURE_COLUMNS]
    y = df["yield_kg_ha"]
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    lgb_model = _train_lightgbm(X_train, y_train)
    xgb_model = _train_xgboost(X_train, y_train)

    lgb_mae = mean_absolute_error(y_test, lgb_model.predict(X_test))
    xgb_mae = mean_absolute_error(y_test, xgb_model.predict(X_test))

    if lgb_mae <= xgb_mae:
        champion_name, champion_model, champion_mae = "lightgbm", lgb_model, lgb_mae
        challenger_name, challenger_mae = "xgboost", xgb_mae
    else:
        champion_name, champion_model, champion_mae = "xgboost", xgb_model, xgb_mae
        challenger_name, challenger_mae = "lightgbm", lgb_mae

    quantile_models = {
        0.1: _train_quantile_lightgbm(X_train, y_train, 0.1),
        0.5: _train_quantile_lightgbm(X_train, y_train, 0.5),
        0.9: _train_quantile_lightgbm(X_train, y_train, 0.9),
    }

    trained = TrainedCropModel(
        crop=key,
        champion_name=champion_name,
        champion_model=champion_model,
        quantile_models=quantile_models,
        challenger_name=challenger_name,
        challenger_mae=round(float(challenger_mae), 1),
        champion_mae=round(float(champion_mae), 1),
        trained_at=datetime.now(timezone.utc).isoformat(),
        version=f"global-bootstrap-{key}-v1",
        feature_columns=FEATURE_COLUMNS,
    )
    _REGISTRY[key] = trained
    return trained
