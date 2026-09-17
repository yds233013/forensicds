"""Panel regression with store and week fixed effects (house method since the ESL readout)."""
from __future__ import annotations

import numpy as np
import pandas as pd


def _demean(df: pd.DataFrame, cols, iters: int = 50) -> pd.DataFrame:
    out = df[cols].astype(float).copy()
    for _ in range(iters):
        out -= out.groupby(df["store_id"]).transform("mean")
        out -= out.groupby(df["week_start"]).transform("mean")
    return out


def _fit(df: pd.DataFrame, y: str, xs) -> tuple[np.ndarray, np.ndarray]:
    d = df[df["comparable"] == 1]
    dm = _demean(d, [y] + list(xs))
    X, Y = dm[list(xs)].to_numpy(), dm[y].to_numpy()
    beta = np.linalg.lstsq(X, Y, rcond=None)[0]
    resid = Y - X @ beta
    bread = np.linalg.inv(X.T @ X)
    meat = np.zeros((len(xs), len(xs)))
    for _, idx in d.groupby("store_id").indices.items():
        g = X[idx].T @ resid[idx]
        meat += np.outer(g, g)
    vcov = bread @ meat @ bread
    return beta, np.sqrt(np.diag(vcov))


def twfe(panel: pd.DataFrame, outcome: str) -> dict:
    beta, se = _fit(panel, outcome, ["treated"])
    return {"estimate": float(beta[0]), "se": float(se[0])}


def twfe_by_wave(panel: pd.DataFrame, outcome: str) -> dict:
    p = panel.copy()
    waves = sorted(p.loc[p["go_live_week"].notna(), "wave"].unique())
    xs = []
    for w in waves:
        col = f"treated_w{w}"
        p[col] = ((p["wave"] == w) & (p["treated"] == 1)).astype(int)
        xs.append(col)
    beta, se = _fit(p, outcome, xs)
    return {str(int(w)): {"estimate": float(b), "se": float(s)} for w, b, s in zip(waves, beta, se)}
