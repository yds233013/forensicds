"""Assemble the feature matrix (one row per example)."""
from __future__ import annotations

import pandas as pd

from renewal_risk.features import contract, health, pipeline_signals, support, usage
from renewal_risk.features.registry import FEATURE_COLUMNS
from renewal_risk.sources.warehouse import Warehouse

BUILDERS = [contract.build, usage.build, support.build, pipeline_signals.build, health.build]


def build_features(examples: pd.DataFrame, wh: Warehouse) -> pd.DataFrame:
    out = examples[["contract_id", "prediction_date"]].copy()
    for builder in BUILDERS:
        part = builder(examples, wh)
        if part["contract_id"].duplicated().any() or len(part) != len(examples):
            raise ValueError(f"{builder.__module__} returned a different number of rows than examples")
        out = out.merge(part, on="contract_id", how="left", validate="one_to_one")
    return out[["contract_id", "prediction_date"] + FEATURE_COLUMNS]
