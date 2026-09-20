"""G34 REDESIGN: crude-risk / competing-risks core (research only).

BUSINESS QUESTION (Q1, crude risk, current policy)
  Of units now in service, what fraction will suffer an unplanned failure of the critical
  assembly before age 36 months UNDER THE CURRENT MAINTENANCE POLICY? Drives spare-assembly
  stocking and field-service staffing for the coming year.

SECOND QUESTION (Q2, net reliability)
  If overhauls were deferred, what fraction of assemblies would fail by 36 months? Drives the
  engineering case for changing the overhaul interval.

The SAME event history answers both, but a retirement or an overhaul plays a DIFFERENT
statistical role in each:

  event                 role for Q1 (crude)        role for Q2 (net)
  unplanned_failure     target event               target event
  planned_overhaul      COMPETING EVENT            censoring
  unit_retirement       COMPETING EVENT            censoring
  facility_transfer     NOT AN EXIT                NOT AN EXIT
  telemetry_outage      NOT AN EXIT                NOT AN EXIT
  extract_end           censoring                  censoring
"""
from __future__ import annotations
import copy
import numpy as np

H = 36.0

BASE = {
    "name": "visible",
    "n_units": 25000,
    "study_months": 84.0,
    "wb_shape": 2.2, "wb_scale": 40.0, "frailty_sd": 0.40,
    "overhaul_age": 24.0, "overhaul_slack": 4.0,
    "retire_scale": 70.0, "retire_shape": 1.6,     # age-based retirement, condition-independent
    "p_transfer": 0.14,                            # unit moves site, keeps its assembly
    "p_outage": 0.22,                              # telemetry gap, unit keeps running
    "gate": 0.28,                                  # stock the larger spares pool iff Q1 > 0.28
}

REGIMES = {
    "visible": {},
    "failure_heavy": {"wb_scale": 31.0},
    "overhaul_heavy": {"overhaul_age": 16.0},
    "retirement_heavy": {"retire_scale": 38.0},
    "mixed_low_risk": {"wb_scale": 52.0, "overhaul_age": 30.0},
}


def regime(name):
    s = copy.deepcopy(BASE); s.update(copy.deepcopy(REGIMES[name])); s["name"] = name
    return s


def draw_world(spec, seed):
    rng = np.random.default_rng(seed)
    n = spec["n_units"]
    frail = rng.lognormal(0, spec["frailty_sd"], n)
    Tf = spec["wb_scale"] * rng.weibull(spec["wb_shape"], n) / frail ** (1 / spec["wb_shape"])
    Toh = spec["overhaul_age"] + rng.exponential(spec["overhaul_slack"], n)
    Tret = spec["retire_scale"] * rng.weibull(spec["retire_shape"], n)
    comm = rng.uniform(0, spec["study_months"], n)
    Tadm = spec["study_months"] - comm
    Ttr = np.where(rng.random(n) < spec["p_transfer"], rng.uniform(1, 60, n), np.inf)
    out_s = np.where(rng.random(n) < spec["p_outage"], rng.uniform(1, 60, n), np.inf)
    exit_ = np.minimum.reduce([Tf, Toh, Tret, Tadm])
    cause = np.select([(Tf <= Toh) & (Tf <= Tret) & (Tf <= Tadm),
                       (Toh <= Tret) & (Toh <= Tadm),
                       (Tret <= Tadm)], [1, 2, 3], default=0)
    return dict(spec=spec, seed=seed, Tf=Tf, Toh=Toh, Tret=Tret, Tadm=Tadm, comm=comm,
                exit=exit_, cause=cause, transfer=Ttr, outage=out_s)


def truth(w):
    """Q1 crude CIF: first terminal event is an unplanned failure, occurring by H.
       Q2 net: marginal probability the assembly fails by H, overhaul/retirement absent."""
    Tf, Toh, Tret = w["Tf"], w["Toh"], w["Tret"]
    q1 = float(np.mean((Tf <= H) & (Tf < Toh) & (Tf < Tret)))
    q2 = float(np.mean(Tf <= H))
    return {"q1_crude_cif": q1, "q2_net_risk": q2,
            "decision": "stock_high" if q1 > w["spec"]["gate"] else "stock_base"}


CODE = {1: "UNPL_FAIL", 2: "PM_OVHL", 3: "ASSET_RET", 0: "EXTRACT_END"}


def observed(w):
    """Work-order style records. Transfers and outages appear as their own rows and do NOT end
    the unit's exposure; the analyst must decide that from the asset history."""
    rows = []
    for i in range(len(w["exit"])):
        ev = []
        if w["transfer"][i] < w["exit"][i]:
            ev.append({"age_months": float(w["transfer"][i]), "code": "SITE_XFER"})
        if w["outage"][i] < w["exit"][i]:
            ev.append({"age_months": float(w["outage"][i]), "code": "TELEM_GAP"})
        ev.append({"age_months": float(w["exit"][i]), "code": CODE[int(w["cause"][i])]})
        rows.append({"unit_id": int(i), "events": sorted(ev, key=lambda e: e["age_months"])})
    return {"spec": w["spec"], "units": rows, "horizon": H, "gate": w["spec"]["gate"]}
