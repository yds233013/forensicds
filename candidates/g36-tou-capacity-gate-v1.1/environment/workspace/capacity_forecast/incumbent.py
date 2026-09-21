"""Incumbent residential peak-load forecast.

Per-segment weighted least squares of peak-window load on cooling degree days, fitted on the
flat-tariff history and standardised over the current estate and the published weather forecast.

This model has been in production for two planning cycles. Its holdout performance on a withheld
summer is documented in reports/peak_forecast_backtest.md.
"""
from __future__ import annotations

import numpy as np

PILOT_YEAR = 2026


def fit_and_forecast(frames):
    df = frames["loads"]
    hist = df[df["year"] != PILOT_YEAR]
    shares = frames["customers"]["segment_code"].value_counts(normalize=True).sort_index()
    tcdd = frames["forecast"]["cooling_degree_days_forecast"].to_numpy(float)

    total, seg_fc = 0.0, {}
    for s in shares.index:
        h = hist[hist["segment_code"] == s]
        g = h.groupby("cooling_degree_days")["peak_kw"]
        m, n = g.mean(), g.size()
        X = np.column_stack([np.ones(len(m)), m.index.to_numpy(float)])
        sw = np.sqrt(n.to_numpy(float))
        a, b = np.linalg.lstsq(X * sw[:, None], m.to_numpy(float) * sw, rcond=None)[0]
        fc = float(np.mean(a + b * tcdd))
        seg_fc[s] = fc
        total += float(shares[s]) * fc
    return dict(target_peak_kw=total, segment_target_peak_kw=seg_fc,
                shares={k: float(v) for k, v in shares.items()},
                target_cdd_mean=float(tcdd.mean()))
