"""G01 v2 Phase-0 generator: collections episodes, cure timing, payment posting, file deliveries (research only).

Everything is a function of value dates and system state. Labels are deterministic; the question the task poses is
which episodes may be evaluated at all.
"""
from __future__ import annotations

import copy

import numpy as np

DAY = np.timedelta64(1, "D")

BASE = {
    "name": "visible",
    "months": 20,                      # entry months
    "inhouse_per_month": 2600,
    "acquired_from_month": 8,
    "acquired_per_month": 1500,
    "dev_auc": 0.742,
    "delta_inhouse": 0.0,              # logit shift of true cure probability
    "delta_acquired": 0.0,
    "decay_from_month": None,          # month from which the score loses information
    "decay_factor": 1.0,
    "policy_from_month": 9,            # early-contact escalation for high scores
    "policy_threshold": 0.45,
    "cure_median_day": 16,
    "cure_median_day_early": 4,
    "hub_lag": {"dd_card": (0, 1, 0.62), "transfer": (1, 4, 0.30), "branch": (2, 6, 0.08)},
    "hub_close_lag_days": 6,           # watermark = extract - 6 days
    "servicer_load_day": 24,           # coverage month M posts on the 24th of M+1
    "held_month_offset": -3,           # which coverage month is held (relative to the last full month)
    "extract_day": 15,                 # extract taken on the 15th of the month after the last entry month
    "status_retire_drop": 0.05,
    "status_calib_gap": 0.06,
    "status_vintages": 3,              # status is read from the most recent evaluable vintages
}

REGIMES = {
    "visible": {},
    "acquired_miscalibrated": {"delta_acquired": -0.55},          # truth: recalibrate
    "score_decay": {"decay_from_month": 12, "decay_factor": 0.25},  # truth: retire
    "late_cadence": {"servicer_load_day": 20, "held_month_offset": -2, "hub_close_lag_days": 9},
}


def regime(name):
    s = copy.deepcopy(BASE)
    s.update(REGIMES[name])
    s["name"] = name
    return s


def _logit(p):
    p = np.clip(p, 1e-6, 1 - 1e-6)
    return np.log(p / (1 - p))


def _expit(x):
    return 1 / (1 + np.exp(-x))


def draw_world(spec, seed):
    rng = np.random.default_rng(seed)
    start = np.datetime64("2025-01-01")
    rows = []
    for m in range(spec["months"]):
        month_start = start + np.timedelta64(m * 31, "D")
        month_start = month_start.astype("datetime64[M]").astype("datetime64[D]")
        for portfolio, n in (("in_house", spec["inhouse_per_month"]),
                             ("acquired", spec["acquired_per_month"] if m >= spec["acquired_from_month"] else 0)):
            if not n:
                continue
            entry = month_start + rng.integers(0, 28, n) * DAY
            rows.append((portfolio, m, entry))
    portfolio = np.concatenate([np.full(len(e), p) for p, _, e in rows])
    month = np.concatenate([np.full(len(e), m) for _, m, e in rows])
    entry = np.concatenate([e for _, _, e in rows])
    N = len(entry)
    score = np.clip(rng.beta(2, 3, N), 1e-4, 1 - 1e-4)

    # true cure probability: calibrated, with optional portfolio shift and optional discrimination decay
    lo = _logit(score) + np.where(portfolio == "acquired", spec["delta_acquired"], spec["delta_inhouse"])
    if spec["decay_from_month"] is not None:
        dec = month >= spec["decay_from_month"]
        lo = np.where(dec, spec["decay_factor"] * _logit(score) + (1 - spec["decay_factor"]) * _logit(np.full(N, 0.4)), lo)
    p_cure = _expit(lo)
    cured = rng.random(N) < p_cure

    # escalation policy: high scores after policy_from_month are contacted early -> they cure sooner in the window
    early = (month >= spec["policy_from_month"]) & (score >= spec["policy_threshold"])
    med = np.where(early, spec["cure_median_day_early"], spec["cure_median_day"])
    shape = 2.0
    day = rng.gamma(shape, med / shape, N)
    cure_day = np.clip(np.round(day), 1, 30).astype(int)

    # payments: cured episodes clear arrears on the cure day; others make a partial payment that never clears
    value_date = entry + cure_day * DAY
    channels = list(spec["hub_lag"])
    probs = np.array([spec["hub_lag"][c][2] for c in channels]); probs = probs / probs.sum()
    ch = rng.choice(len(channels), N, p=probs)
    lag = np.zeros(N, int)
    for i, c in enumerate(channels):
        a, b, _ = spec["hub_lag"][c]
        m = ch == i
        lag[m] = rng.integers(a, b + 1, m.sum())
    hub_post = value_date + lag * DAY

    # servicer: coverage month of the value date posts on load day of the following month
    vd_month = value_date.astype("datetime64[M]")
    load = (vd_month + 1).astype("datetime64[D]") + (spec["servicer_load_day"] - 1) * DAY
    posted = np.where(portfolio == "acquired", load, hub_post)

    last_entry_month = (start.astype("datetime64[M]") + spec["months"] - 1)
    extract = (last_entry_month + 1).astype("datetime64[D]") + (spec["extract_day"] - 1) * DAY
    hub_watermark = extract - spec["hub_close_lag_days"] * DAY

    # servicer coverage: every month with load <= extract, except the held month
    months_all = np.arange(start.astype("datetime64[M]"), (last_entry_month + 2).astype("datetime64[M]"))
    loads = (months_all + 1).astype("datetime64[D]") + (spec["servicer_load_day"] - 1) * DAY
    delivered = months_all[loads <= extract]
    held = delivered[spec["held_month_offset"]] if len(delivered) >= abs(spec["held_month_offset"]) else None
    loaded_months = np.array([m for m in delivered if m != held])

    observed = posted <= extract                      # payment visible in the extract
    window_end = entry + 30 * DAY
    # evaluability: every value date in the window is known complete for the source that owes it
    if len(loaded_months):
        cov = set(loaded_months.astype(str))
    else:
        cov = set()
    wm_start = entry.astype("datetime64[M]").astype(str)
    wm_end = window_end.astype("datetime64[M]").astype(str)
    acq_ok = np.array([(a in cov) and (b in cov) for a, b in zip(wm_start, wm_end)])
    evaluable = np.where(portfolio == "acquired", acq_ok, window_end <= hub_watermark)

    return dict(spec=spec, seed=seed, N=N, portfolio=portfolio, month=month, entry=entry, score=score,
                cured=cured, cure_day=cure_day, value_date=value_date, posted=posted, observed=observed,
                extract=extract, hub_watermark=hub_watermark, loaded_months=loaded_months, held=held,
                window_end=window_end, evaluable=evaluable, early=early)


def auc(score, y):
    y = np.asarray(y, bool)
    if y.all() or (~y).any() is False or y.sum() == 0 or (~y).sum() == 0:
        return float("nan")
    order = np.argsort(score)
    ranks = np.empty(len(score), float)
    ranks[order] = np.arange(1, len(score) + 1)
    n1, n0 = y.sum(), (~y).sum()
    return float((ranks[y].sum() - n1 * (n1 + 1) / 2) / (n1 * n0))


def status(spec, a, gap):
    if np.isnan(a):
        return "undetermined"
    if a < spec["dev_auc"] - spec["status_retire_drop"]:
        return "retire"
    if abs(gap) > spec["status_calib_gap"]:
        return "recalibrate"
    return "keep"


def recent_vintages(w, mask, k):
    """The k most recent entry months that have any rows in `mask`."""
    ms = np.unique(w["month"][mask])
    return set(ms[-k:].tolist()) if len(ms) else set()


def truth(w):
    """Deterministic truth: metrics over the evaluable population, with true labels."""
    spec = w["spec"]
    m = w["evaluable"]
    a = auc(w["score"][m], w["cured"][m])
    gap = float(w["score"][m].mean() - w["cured"][m].mean())
    out = {"n_evaluable": int(m.sum()), "auc": a, "calib_gap": gap, "status": status(spec, a, gap)}
    for p in ("in_house", "acquired"):
        q = m & (w["portfolio"] == p)
        out[f"auc_{p}"] = auc(w["score"][q], w["cured"][q])
        out[f"gap_{p}"] = float(w["score"][q].mean() - w["cured"][q].mean())
    recent = recent_vintages(w, m, spec["status_vintages"])
    r = m & np.isin(w["month"], list(recent))
    out["recent_vintages"] = sorted(recent)
    out["recent_auc"] = auc(w["score"][r], w["cured"][r])
    out["recent_gap"] = float(w["score"][r].mean() - w["cured"][r].mean())
    out["status"] = status(spec, out["recent_auc"], out["recent_gap"])
    return out
