"""Evaluation metrics (definitions: docs/monitoring/lead_score_evaluation.md)."""
from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score


def score_bins(cohort: pd.DataFrame, n_bins: int) -> list[pd.DataFrame]:
    """Equal-count bins by ascending score (ties broken by lead_id)."""
    ordered = cohort.sort_values(["score", "lead_id"], kind="mergesort").reset_index(drop=True)
    return [ordered.iloc[idx] for idx in np.array_split(np.arange(len(ordered)), n_bins)]


def compute_metrics(cohort: pd.DataFrame, n_bins: int, target_rate: float) -> dict:
    y = cohort["label"].to_numpy()
    s = cohort["score"].to_numpy()
    overall = float(y.mean())
    bins = score_bins(cohort, n_bins)
    calibration = [{"bin": i + 1, "n": int(len(b)), "min_score": float(b["score"].min()), "max_score": float(b["score"].max()),
                    "mean_score": float(b["score"].mean()), "conversion_rate": float(b["label"].mean())}
                   for i, b in enumerate(bins)]
    top = bins[-1]
    recommended = None
    for row in reversed(calibration):
        if row["conversion_rate"] >= target_rate:
            recommended = row["min_score"]
        else:
            break
    by_source = {src: {"n": int(len(g)), "conversion_rate": float(g["label"].mean())}
                 for src, g in cohort.groupby("source")}
    return {
        "n_leads": int(len(cohort)),
        "n_converted": int(y.sum()),
        "conversion_rate": overall,
        "roc_auc": float(roc_auc_score(y, s)),
        "top_decile_conversion_rate": float(top["label"].mean()),
        "top_decile_lift": float(top["label"].mean() / overall),
        "calibration": calibration,
        "recommended_threshold": recommended,
        "by_source": by_source,
    }
