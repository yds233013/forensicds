"""Model training (specification: docs/model_card_renewal_risk.md, section Model)."""
from __future__ import annotations

import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from renewal_risk.config import Config
from renewal_risk.features.registry import FEATURE_COLUMNS
from renewal_risk.model.transforms import Winsorizer


def make_model(cfg: Config) -> Pipeline:
    return Pipeline([
        ("winsorize", Winsorizer(cfg.winsor_lower, cfg.winsor_upper)),
        ("scale", StandardScaler()),
        ("clf", LogisticRegression(C=cfg.model_C, class_weight=cfg.class_weight, max_iter=cfg.max_iter, solver="lbfgs")),
    ])


def train(features: pd.DataFrame, labels: pd.Series, cfg: Config) -> Pipeline:
    model = make_model(cfg)
    model.fit(features[FEATURE_COLUMNS].to_numpy(dtype=float), labels.to_numpy())
    return model


def predict(model: Pipeline, features: pd.DataFrame):
    return model.predict_proba(features[FEATURE_COLUMNS].to_numpy(dtype=float))[:, 1]
