"""G01 v2 Phase-0 analyses: the reference (accepted) rule and the natural wrong analyses (research only).

Each analysis returns the population it would evaluate, the labels it would use, and the resulting metrics/status.
"""
from __future__ import annotations

import numpy as np

import g01_sim as S

DAY = np.timedelta64(1, "D")


def _metrics(w, mask, label):
    spec = w["spec"]
    out = {"n_evaluable": int(mask.sum())}
    for p in ("in_house", "acquired"):
        q = mask & (w["portfolio"] == p)
        out[f"auc_{p}"] = S.auc(w["score"][q], label[q]) if q.sum() > 50 else float("nan")
        out[f"gap_{p}"] = float(w["score"][q].mean() - label[q].mean()) if q.sum() > 50 else float("nan")
    out["auc"] = S.auc(w["score"][mask], label[mask])
    out["calib_gap"] = float(w["score"][mask].mean() - label[mask].mean())
    recent = S.recent_vintages(w, mask, spec["status_vintages"])
    r = mask & np.isin(w["month"], list(recent))
    out["recent_vintages"] = sorted(recent)
    out["recent_auc"] = S.auc(w["score"][r], label[r]) if r.sum() > 50 else float("nan")
    out["recent_gap"] = float(w["score"][r].mean() - label[r].mean()) if r.sum() > 50 else float("nan")
    out["status"] = S.status(spec, out["recent_auc"], out["recent_gap"])
    return out


def _label_value_date(w):
    """cure_30d from value-dated payments present in the extract."""
    return w["cured"] & (w["cure_day"] <= 30) & w["observed"]


def _label_posting_date(w):
    """the faulty job: the payment must have POSTED within the 30-day window."""
    return w["cured"] & w["observed"] & ((w["posted"] - w["entry"]) / DAY <= 30)


# ----------------------------------------------------------------- accepted
def accepted_reference(w):
    """Value-date labels; evaluable = every value date in the window known complete for its source."""
    return _metrics(w, w["evaluable"], _label_value_date(w))


def accepted_sql_style(w):
    """Same rule, expressed as coverage sets rather than per-row conditions (structurally different, same answer)."""
    cov = set(w["loaded_months"].astype(str))
    acq = np.array([(a in cov) and (b in cov) for a, b in
                    zip(w["entry"].astype("datetime64[M]").astype(str), w["window_end"].astype("datetime64[M]").astype(str))])
    hub = w["window_end"] <= w["hub_watermark"]
    mask = np.where(w["portfolio"] == "acquired", acq, hub)
    lab = w["cured"] & (w["cure_day"] <= 30) & (w["posted"] <= w["extract"])
    return _metrics(w, mask, lab)


# ----------------------------------------------------------------- wrong
def w1_posting_label_30d_maturity(w):
    """Keep posting-date labels; evaluate entries older than 30 days."""
    mask = (w["extract"] - w["entry"]) / DAY > 30
    return _metrics(w, mask, _label_posting_date(w))


def w2_value_label_global_maturity(w):
    """Value-date labels, but maturity is a global 30-day age rule."""
    mask = (w["extract"] - w["entry"]) / DAY > 30
    return _metrics(w, mask, _label_value_date(w))


def w2b_value_label_global_60(w):
    """Value-date labels with a conservative 60-day buffer."""
    mask = (w["extract"] - w["entry"]) / DAY > 60
    return _metrics(w, mask, _label_value_date(w))


def w3_max_coverage_watermark(w):
    """Per-source watermark taken as the maximum coverage end (ignores the held month)."""
    if len(w["loaded_months"]):
        end = (w["loaded_months"].max() + 1).astype("datetime64[D]") - DAY
    else:
        end = w["entry"].min()
    acq = w["window_end"] <= end
    hub = w["window_end"] <= w["hub_watermark"]
    mask = np.where(w["portfolio"] == "acquired", acq, hub)
    return _metrics(w, mask, _label_value_date(w))


def w4_empirical_lag_watermark(w):
    """Watermark from the observed posting-lag distribution (99th percentile per source)."""
    lag = (w["posted"] - w["value_date"]) / DAY
    mask = np.zeros(w["N"], bool)
    for p in ("in_house", "acquired"):
        q = w["portfolio"] == p
        lag_p = np.percentile(lag[q & w["observed"]], 99)
        mask |= q & (w["window_end"] <= w["extract"] - lag_p * DAY)
    return _metrics(w, mask, _label_value_date(w))


def w5_contiguous_coverage(w):
    """Servicer coverage taken as contiguous months from the first delivered file (drops post-gap windows)."""
    months = np.sort(w["loaded_months"])
    keep = []
    for i, m in enumerate(months):
        if i == 0 or (m - months[i - 1]).astype(int) == 1:
            keep.append(m)
        else:
            break
    cov = set(np.array(keep).astype(str)) if keep else set()
    acq = np.array([(a in cov) and (b in cov) for a, b in
                    zip(w["entry"].astype("datetime64[M]").astype(str), w["window_end"].astype("datetime64[M]").astype(str))])
    hub = w["window_end"] <= w["hub_watermark"]
    mask = np.where(w["portfolio"] == "acquired", acq, hub)
    return _metrics(w, mask, _label_value_date(w))


def w6_label_determined_population(w):
    """Correct labels and watermarks, but the population is 'labels we already know'."""
    lab = _label_value_date(w)
    determined = lab | w["evaluable"]          # cured-and-posted, or window complete
    return _metrics(w, determined, lab)


def w7_exclude_acquired(w):
    """Drop the acquired portfolio as a 'broken feed'."""
    mask = w["evaluable"] & (w["portfolio"] == "in_house")
    return _metrics(w, mask, _label_value_date(w))


def w8_all_scored(w):
    """Evaluate every scored episode with whatever is observed."""
    return _metrics(w, np.ones(w["N"], bool), _label_value_date(w))


def w9_determined_or_mature(w):
    """Partial repair: value-date labels, global maturity, plus early-cured rows kept."""
    lab = _label_value_date(w)
    mask = ((w["extract"] - w["entry"]) / DAY > 30) | lab
    return _metrics(w, mask, lab)


ACCEPTED = {"reference": accepted_reference, "sql_style": accepted_sql_style}
WRONG = {"w1_posting_label_30d": w1_posting_label_30d_maturity,
         "w2_value_global_30": w2_value_label_global_maturity,
         "w2b_value_global_60": w2b_value_label_global_60,
         "w3_max_coverage": w3_max_coverage_watermark,
         "w4_empirical_lag": w4_empirical_lag_watermark,
         "w5_contiguous_coverage": w5_contiguous_coverage,
         "w6_label_determined": w6_label_determined_population,
         "w7_exclude_acquired": w7_exclude_acquired,
         "w8_all_scored": w8_all_scored,
         "w9_determined_or_mature": w9_determined_or_mature}
