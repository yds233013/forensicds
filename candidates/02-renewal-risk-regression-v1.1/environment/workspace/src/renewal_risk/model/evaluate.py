"""Offline evaluation metrics."""
from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.metrics import average_precision_score, brier_score_loss, log_loss, roc_auc_score


def calibration_table(labels: np.ndarray, scores: np.ndarray, bins: int) -> list[dict]:
    order = np.argsort(scores, kind="stable")
    rows = []
    for i, idx in enumerate(np.array_split(order, bins)):
        if len(idx) == 0:
            continue
        rows.append({"bin": i + 1, "n": int(len(idx)), "mean_score": round(float(scores[idx].mean()), 6),
                     "churn_rate": round(float(labels[idx].mean()), 6)})
    return rows


def evaluate(predictions: pd.DataFrame, bins: int) -> dict:
    y = predictions["label"].to_numpy()
    s = predictions["score"].to_numpy()
    metrics = {
        "n_eval": int(len(y)),
        "eval_churn_rate": round(float(y.mean()), 6),
        "roc_auc": float(roc_auc_score(y, s)),
        "pr_auc": float(average_precision_score(y, s)),
        "brier": float(brier_score_loss(y, s)),
        "log_loss": float(log_loss(y, s)),
        "calibration": calibration_table(y, s, bins),
        "by_segment": {},
    }
    for seg, g in predictions.groupby("segment"):
        if g["label"].nunique() == 2:
            metrics["by_segment"][seg] = {"n": int(len(g)), "roc_auc": float(roc_auc_score(g["label"], g["score"]))}
    return metrics
