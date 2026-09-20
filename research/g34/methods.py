"""G34: valid estimator families, pre-registered wrong methods, cheap-solve panel."""
from __future__ import annotations
import numpy as np
import simulation as S

A, B = S.A_WINDOW, S.B_WINDOW


def _arrays(ob, origin="commissioned", truncate=True, treat=("unplanned_failure",),
            censor_extra=(), drop_sensor_gap=False):
    e, x, ev = [], [], []
    for r in ob["units"]:
        if drop_sensor_gap and r["sensor_gap"]:
            continue
        o = r["commissioned_month"] if origin == "commissioned" else r["monitoring_from_month"]
        ent = (r["monitoring_from_month"] - o) if truncate else 0.0
        xt = r["last_seen_month"] - o
        reason = r["removal_reason"]
        k = 1 if reason in treat else (1 if reason in censor_extra else 0)
        e.append(ent); x.append(xt); ev.append(k)
    return np.array(e), np.array(x), np.array(ev, int)


def _km(entry, exit_, ev, a=A, b=B):
    m = (ev == 1) & (exit_ > a) & (exit_ <= b)
    if not m.any():
        return 0.0
    t = np.unique(exit_[m])
    d = np.array([np.count_nonzero((exit_ == q) & (ev == 1)) for q in t])
    n = np.array([np.count_nonzero((entry < q) & (exit_ >= q)) for q in t])
    return 1 - float(np.prod(1 - d / np.maximum(n, 1)))


def _pack(p, ob):
    return {"p_fail_18_30": float(p), "decision": "extend" if p < ob["gate"] else "hold"}


# ----------------------------------------------------------------- VALID
def V1_km_age_lefttrunc(ob):
    """Kaplan-Meier on the age clock with delayed entry; overhaul and decommission censored."""
    return _pack(_km(*_arrays(ob)), ob)


def V2_actuarial_lifetable(ob):
    """Monthly life-table on the age clock, with the actuarial half-interval adjustment for
    entries and censorings that occur inside an interval. Without that adjustment this estimator
    is biased downward whenever censoring is heavy inside the window - which it is here, because
    the planned overhaul falls at the start of the decision window."""
    entry, exit_, ev = _arrays(ob)
    surv = 1.0
    for m0 in np.arange(A, B, 1.0):
        m1 = m0 + 1
        at_start = np.count_nonzero((entry <= m0) & (exit_ > m0))
        entering = np.count_nonzero((entry > m0) & (entry < m1) & (exit_ > m0))
        d = np.count_nonzero((ev == 1) & (exit_ > m0) & (exit_ <= m1))
        cens = np.count_nonzero((ev != 1) & (exit_ > m0) & (exit_ <= m1))
        n_eff = at_start + 0.5 * entering - 0.5 * cens
        if n_eff > 0:
            surv *= (1 - d / n_eff)
    return _pack(1 - surv, ob)


def V3_weibull_mle(ob):
    """Parametric Weibull fitted by left-truncated, right-censored likelihood."""
    entry, exit_, ev = _arrays(ob)
    from scipy.optimize import minimize

    def nll(th):
        k, lam = np.exp(th)
        H = lambda t: (np.maximum(t, 1e-9) / lam) ** k
        ll = np.sum(ev * (np.log(k / lam) + (k - 1) * np.log(np.maximum(exit_, 1e-9) / lam)))
        ll -= np.sum(H(exit_) - H(entry))
        return -ll
    r = minimize(nll, np.log([2.0, 30.0]), method="Nelder-Mead",
                 options={"maxiter": 800, "xatol": 1e-4, "fatol": 1e-4})
    k, lam = np.exp(r.x)
    S_ = lambda t: np.exp(-(t / lam) ** k)
    return _pack(1 - S_(B) / S_(A), ob)


VALID = {"V1_km_age_lefttrunc": V1_km_age_lefttrunc, "V2_actuarial_lifetable": V2_actuarial_lifetable,
         "V3_weibull_mle": V3_weibull_mle}


# ----------------------------------------------------------------- WRONG
def W1_no_truncation(ob):
    """Age clock, but every unit treated as observed from age 0."""
    return _pack(_km(*_arrays(ob, truncate=False)), ob)


def W2_monitoring_clock(ob):
    """Time origin = monitoring go-live instead of commissioning."""
    return _pack(_km(*_arrays(ob, origin="monitoring")), ob)


def W3_naive_rate(ob):
    entry, exit_, ev = _arrays(ob)
    pt = np.clip(np.minimum(exit_, B) - np.maximum(entry, A), 0, None).sum()
    nf = np.count_nonzero((ev == 1) & (exit_ > A) & (exit_ <= B))
    return _pack(1 - np.exp(-(nf / max(pt, 1e-9)) * (B - A)), ob)


def W4_mature_only(ob):
    """Only units whose whole life is inside the monitoring window."""
    sub = {"units": [r for r in ob["units"] if r["commissioned_month"] >= ob["mon_start"]],
           "mon_start": ob["mon_start"], "gate": ob["gate"], "spec": ob["spec"],
           "study_end": ob["study_end"]}
    if len(sub["units"]) < 50:
        return _pack(float("nan"), ob)
    return _pack(_km(*_arrays(sub)), ob)


def W5_overhaul_as_event(ob):
    """Planned overhaul counted as a failure."""
    return _pack(_km(*_arrays(ob, censor_extra=("planned_overhaul",))), ob)


def W6_drop_censored(ob):
    entry, exit_, ev = _arrays(ob)
    k = ev == 1
    return _pack(float(np.mean((exit_[k] > A) & (exit_[k] <= B))) if k.any() else float("nan"), ob)


def W7_raw_event_fraction(ob):
    entry, exit_, ev = _arrays(ob)
    inw = exit_ > A
    return _pack(float(np.mean((ev[inw] == 1) & (exit_[inw] <= B))) if inw.any() else float("nan"), ob)


def W8_drop_sensor_gap_units(ob):
    """Treat a monitoring gap as loss of the unit and drop those rows."""
    return _pack(_km(*_arrays(ob, drop_sensor_gap=True)), ob)


def W9_decom_as_event(ob):
    """Site decommission counted as a failure."""
    return _pack(_km(*_arrays(ob, censor_extra=("site_decommission",))), ob)


WRONG = {"W1_no_truncation": W1_no_truncation, "W2_monitoring_clock": W2_monitoring_clock,
         "W3_naive_rate": W3_naive_rate, "W4_mature_only": W4_mature_only,
         "W5_overhaul_as_event": W5_overhaul_as_event, "W6_drop_censored": W6_drop_censored,
         "W7_raw_event_fraction": W7_raw_event_fraction,
         "W8_drop_sensor_gap_units": W8_drop_sensor_gap_units, "W9_decom_as_event": W9_decom_as_event}


# ----------------------------------------------------------------- CHEAP-SOLVE PANEL
def C_constant_hold(ob):
    return {"p_fail_18_30": float("nan"), "decision": "hold"}


def C_constant_extend(ob):
    return {"p_fail_18_30": float("nan"), "decision": "extend"}


def C_failure_share_of_removals(ob):
    rs = [r["removal_reason"] for r in ob["units"] if r["removal_reason"]]
    return _pack(np.mean([x == "unplanned_failure" for x in rs]) if rs else float("nan"), ob)


def C_median_age_at_failure(ob):
    ages = [r["last_seen_month"] - r["commissioned_month"] for r in ob["units"]
            if r["removal_reason"] == "unplanned_failure"]
    return _pack(float(np.mean(np.array(ages) <= B)) if ages else float("nan"), ob)


def C_km_default_no_thought(ob):
    """One-line KM: age clock, no truncation, every removal treated as an event."""
    return _pack(_km(*_arrays(ob, truncate=False,
                              censor_extra=("planned_overhaul", "site_decommission"))), ob)


def C_followup_length_proxy(ob):
    med = np.median([r["last_seen_month"] - r["monitoring_from_month"] for r in ob["units"]])
    return {"p_fail_18_30": float("nan"), "decision": "extend" if med > 12 else "hold"}


def C_oldest_cohort(ob):
    cut = np.quantile([r["commissioned_month"] for r in ob["units"]], 0.25)
    sub = {"units": [r for r in ob["units"] if r["commissioned_month"] <= cut],
           "mon_start": ob["mon_start"], "gate": ob["gate"], "spec": ob["spec"],
           "study_end": ob["study_end"]}
    return _pack(_km(*_arrays(sub)), ob)


CHEAP = {"C_constant_hold": C_constant_hold, "C_constant_extend": C_constant_extend,
         "C_failure_share_of_removals": C_failure_share_of_removals,
         "C_median_age_at_failure": C_median_age_at_failure,
         "C_km_default_no_thought": C_km_default_no_thought,
         "C_followup_length_proxy": C_followup_length_proxy, "C_oldest_cohort": C_oldest_cohort}
