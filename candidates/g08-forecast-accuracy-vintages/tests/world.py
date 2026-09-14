#!/usr/bin/env python3
"""Deterministic synthetic warehouse for ForensicDS G08 (forecast accuracy under settlement vintages).

Writes, under a workspace root:

  data/warehouse.sqlite       settlement runs + status history, forecast issues + values, portfolio membership,
                              models, KPI close log, and the warehouse views the accuracy mart reads
  reports/...                 (visible extract only) signed-off KPI pack history, the September accuracy review
                              produced from the mart, and the ops daily dashboard

Mechanisms: physical volume per region x settlement class x delivery day; settlement runs (EST, IS, R1, R2, RF, DF)
published on a working-day timetable with estimated reads that under-react to temperature; late publication and a
settlement-agent outage; withdrawals followed by re-runs; data-load errors corrected by batch re-runs that supersede
the flawed run; monthly KPI closes (with slips); forecast issues per model and run day (scheduled, pre-gate re-issues
scoped to one region, re-issues that miss the 11:00 UK gate, automatic re-issues after the 06Z weather update);
portfolio restructures effective by delivery date.

Standard library only; fully determined by the spec. Deleted from the image after the build; tests/ holds a copy.
"""
from __future__ import annotations

import copy
import csv
import hashlib
import math
import random
import sqlite3
import sys
from bisect import bisect_left
from collections import defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path

VISIBLE_SPEC: dict = {
    "name": "visible",
    "seed": 80808,
    "delivery_start": "2025-05-20",
    "extract_at": "2026-09-22T06:00:00",
    "first_kpi_month": "2025-07",
    "regions": {"NORTH": 1.10, "MIDLANDS": 1.00, "EAST": 0.80, "SOUTH": 0.90, "WEST": 0.60, "LONDON": 1.30},
    "classes": {
        "DOM": {"base": 3000.0, "season": 0.28, "sat": 1.05, "sun": 1.06, "gamma": -0.022, "est_share": 0.55},
        "SME_NHH": {"base": 900.0, "season": 0.15, "sat": 0.78, "sun": 0.70, "gamma": -0.014, "est_share": 0.45},
        "SME_HH": {"base": 450.0, "season": 0.10, "sat": 0.75, "sun": 0.68, "gamma": -0.009, "est_share": 0.05},
        "IC_HH": {"base": 1800.0, "season": 0.05, "sat": 0.72, "sun": 0.65, "gamma": -0.004, "est_share": 0.02},
        "UMS": {"base": 70.0, "season": 0.35, "sat": 1.0, "sun": 1.0, "gamma": 0.0, "est_share": 0.0},
    },
    # (effective_from delivery date, {portfolio: [classes]}); each structure applies until the next one starts
    "portfolios": [
        ("2025-01-01", {"RESI": ["DOM"], "BUSINESS": ["SME_NHH", "SME_HH", "IC_HH", "UMS"]}),
        ("2026-03-02", {"RESI": ["DOM"], "SME": ["SME_NHH", "SME_HH", "UMS"], "IC": ["IC_HH"]}),
        ("2026-06-01", {"RESI": ["DOM"], "SME": ["SME_NHH", "SME_HH"], "IC": ["IC_HH", "UMS"]}),
    ],
    "horizons": 7,
    "models": [
        {"model": "v3", "first_run": "2025-06-01", "production_from": "2024-02-05", "production_to": "2026-04-05",
         "description": "Regression + ETS ensemble (champion)", "a": 1.00, "u0": 0.029, "uh": 0.0020,
         "auto_reissue": 0.0, "auto_pregate": 0.0, "review_reissue": 0.015},
        {"model": "v4", "first_run": "2026-01-05", "production_from": "2026-04-06", "production_to": None,
         "description": "Gradient-boosted weather model with 06Z auto re-issue", "a": 0.85, "u0": 0.025,
         "uh": 0.0018, "auto_reissue": 0.80, "auto_pregate": 0.0, "review_reissue": 0.0},
    ],
    "weather_w0": 0.016, "weather_wh": 0.0025, "winter_error": 0.35,
    "kappa": 0.018,
    "issuing": {"sched_fail": 0.012, "no_pregate": 0.0025, "partial_pregate": 0.03, "gate_miss": 0.03,
                "gate_miss_partial": 0.5},
    "settlement": {
        "wd": {"IS": 7, "R1": 24, "R2": 80, "RF": 270},
        "late_is": 0.012, "late_is_wd": [3, 12],
        "withdraw": 0.015,
        "dc": {"IS": 0.025, "R1": 0.020},
        "dc_chain": 0.0, "dc_withdrawn": 0.0,
        "df": 0.003,
        "outages": [{"regions": ["MIDLANDS"], "run_type": "IS", "from": "2026-01-19", "to": "2026-01-30",
                     "publish_local": "2026-02-19T11:40:00"}],
        "boundary_cases": {"withdrawn_after_close": 2, "gap_at_close": 2, "dc_after_close": 2, "is_after_close": 2,
                           "dc_before_close": 2},
    },
    "close": {"wd": 12, "hour": 17, "slips": {"2025-12": 2, "2026-04": 1}},
    "migration_month": "2026-07",
    "artifacts": True,
}

KPI_CLOSE_MINUTE_MAX = 50
GROSS_WITHDRAWN = (0.06, 0.12)
DC_DELTA = (0.03, 0.09)

BANK_HOLIDAYS = {date.fromisoformat(s) for s in (
    "2024-01-01 2024-03-29 2024-04-01 2024-05-06 2024-05-27 2024-08-26 2024-12-25 2024-12-26 "
    "2025-01-01 2025-04-18 2025-04-21 2025-05-05 2025-05-26 2025-08-25 2025-12-25 2025-12-26 "
    "2026-01-01 2026-04-03 2026-04-06 2026-05-04 2026-05-25 2026-08-31 2026-12-25 2026-12-28 "
    "2027-01-01 2027-03-26 2027-03-29 2027-05-03 2027-05-31 2027-08-30 2027-12-27 2027-12-28").split()}

RUN_TYPES = ["EST", "IS", "R1", "R2", "RF", "DF"]
EST_SHARE_FACTOR = {"IS": 1.0, "R1": 0.5, "R2": 0.2, "RF": 0.03, "DF": 0.03}


# ------------------------------------------------------------------------------------------------ time helpers


def D(s: str) -> date:
    return date.fromisoformat(s)


def T(s: str) -> datetime:
    return datetime.fromisoformat(s.replace("Z", ""))


def fmt_ts(t: datetime) -> str:
    return t.strftime("%Y-%m-%dT%H:%M:%SZ")


def ym(d: date) -> str:
    return f"{d.year:04d}-{d.month:02d}"


def ym_add(m: str, k: int) -> str:
    y, mo = int(m[:4]), int(m[5:]) - 1 + k
    return f"{y + mo // 12:04d}-{mo % 12 + 1:02d}"


def is_wd(d: date) -> bool:
    return d.weekday() < 5 and d not in BANK_HOLIDAYS


def add_wd(d: date, n: int) -> date:
    while n > 0:
        d += timedelta(days=1)
        if is_wd(d):
            n -= 1
    return d


def nth_wd(y: int, m: int, n: int) -> date:
    d = date(y, m, 1)
    while not is_wd(d):
        d += timedelta(days=1)
    return add_wd(d, n - 1)


def _last_sunday(y: int, m: int) -> date:
    d = (date(y + 1, 1, 1) if m == 12 else date(y, m + 1, 1)) - timedelta(days=1)
    while d.weekday() != 6:
        d -= timedelta(days=1)
    return d


def uk_is_bst(utc: datetime) -> bool:
    start = datetime.combine(_last_sunday(utc.year, 3), datetime.min.time()) + timedelta(hours=1)
    end = datetime.combine(_last_sunday(utc.year, 10), datetime.min.time()) + timedelta(hours=1)
    return start <= utc < end


def local_to_utc(d: date, h: int, mi: int = 0, s: int = 0) -> datetime:
    naive = datetime(d.year, d.month, d.day, h, mi, s)
    cand = naive - timedelta(hours=1)
    return cand if uk_is_bst(cand) else naive


def daterange(a: date, b: date):
    d = a
    while d <= b:
        yield d
        d += timedelta(days=1)


def month_start_end(m: str):
    y, mo = int(m[:4]), int(m[5:])
    start = date(y, mo, 1)
    end = (date(y + 1, 1, 1) if mo == 12 else date(y, mo + 1, 1)) - timedelta(days=1)
    return start, end


def keyed_rng(seed: int, *parts) -> random.Random:
    h = hashlib.sha256(("|".join(map(str, (seed,) + parts))).encode()).digest()
    return random.Random(int.from_bytes(h[:8], "big"))


# ------------------------------------------------------------------------------------------------ world


class World:
    pass


def portfolio_structure(spec, d: date) -> dict:
    cur = None
    for eff, struct in spec["portfolios"]:
        if D(eff) <= d:
            cur = struct
    return cur or {}


def class_active(spec, c: str, d: date) -> bool:
    s = spec["classes"][c].get("start")
    return s is None or d >= D(s)


def generate(spec: dict) -> World:
    w = World()
    w.spec = spec
    rng = random.Random(spec["seed"])
    extract = T(spec["extract_at"])
    w.extract = extract
    horizons = spec["horizons"]
    d0 = D(spec["delivery_start"])
    d_end = extract.date() + timedelta(days=horizons + 2)
    regions = list(spec["regions"])
    classes = list(spec["classes"])

    # ---------------------------------------------------------------- KPI closes
    closes = {}
    m = spec["first_kpi_month"]
    while True:
        nm = ym_add(m, 1)
        slip = spec["close"]["slips"].get(m, 0)
        cd = nth_wd(int(nm[:4]), int(nm[5:]), spec["close"]["wd"] + slip)
        ct = local_to_utc(cd, spec["close"]["hour"], rng.randint(0, KPI_CLOSE_MINUTE_MAX), rng.randint(0, 59))
        if ct > extract + timedelta(days=45):
            break
        closes[m] = ct
        m = nm
    w.closes_all = closes
    w.closes = {k: v for k, v in closes.items() if v <= extract}
    close_times = sorted(closes.values())

    def safe(t: datetime) -> datetime:
        while True:
            i = bisect_left(close_times, t - timedelta(seconds=120))
            if i < len(close_times) and abs((close_times[i] - t).total_seconds()) < 120:
                t += timedelta(seconds=317)
                continue
            return t

    def local_rand(d: date, h0: float, h1: float) -> datetime:
        secs = rng.randint(int(h0 * 3600), int(h1 * 3600))
        return local_to_utc(d, secs // 3600, (secs % 3600) // 60, secs % 60)

    # ---------------------------------------------------------------- physical world
    anom = {r: {} for r in regions}
    nat = 0.0
    reg = {r: 0.0 for r in regions}
    for d in daterange(d0 - timedelta(days=30), d_end):
        nat = 0.8 * nat + rng.gauss(0, 1.3)
        for r in regions:
            reg[r] = 0.6 * reg[r] + rng.gauss(0, 0.8)
            anom[r][d] = nat + reg[r]
    vdet, vtrue = {}, {}
    for r, rscale in spec["regions"].items():
        for c, cp in spec["classes"].items():
            ar = 0.0
            for d in daterange(d0 - timedelta(days=30), d_end):
                ar = 0.7 * ar + rng.gauss(0, 0.0086)
                if not class_active(spec, c, d):
                    continue
                doy = d.timetuple().tm_yday
                season = 1 + cp["season"] * math.cos(2 * math.pi * (doy - 15) / 365.25)
                wd = d.weekday()
                dow = cp["sun"] if (wd == 6 or d in BANK_HOLIDAYS) else cp["sat"] if wd == 5 else 1.0
                ramp = 1.0
                if cp.get("start"):
                    ramp = min(1.0, 0.25 + (d - D(cp["start"])).days / 160)
                base = rscale * cp["base"] * ramp * season * dow * (1 + cp["gamma"] * anom[r][d])
                vdet[(r, c, d)] = base
                vtrue[(r, c, d)] = base * (1 + ar)
    w.vdet, w.anom = vdet, anom

    # ---------------------------------------------------------------- settlement: nominal timetable
    st = spec["settlement"]
    kappa = spec["kappa"]
    nominal = {}  # (r,c,d) -> {type: pub}
    for r in regions:
        for c in classes:
            for d in daterange(d0, extract.date()):
                if not class_active(spec, c, d):
                    continue
                pubs = {"EST": local_rand(d + timedelta(days=1), 4.5, 5.5)}
                for rt, n in st["wd"].items():
                    pubs[rt] = local_rand(add_wd(d, n), 10, 16)
                if rng.random() < st["late_is"]:
                    pubs["IS"] = local_rand(add_wd(pubs["IS"].date(), rng.randint(*st["late_is_wd"])), 10, 16)
                for o in st["outages"]:
                    if r in o["regions"] and D(o["from"]) <= d <= D(o["to"]):
                        base = T(o["publish_local"])
                        pubs[o["run_type"]] = local_to_utc(base.date(), base.hour, base.minute, rng.randint(0, 59))
                if rng.random() < st["df"]:
                    pubs["DF"] = pubs["RF"] + timedelta(days=rng.randint(30, 90), seconds=rng.randint(0, 20000))
                nominal[(r, c, d)] = {k: safe(v) for k, v in pubs.items()}

    modes = {}  # (r,c,d,type) -> mode dict

    # boundary templates (IS chains around KPI closes)
    templates = []
    for kind, n in st.get("boundary_cases", {}).items():
        templates += [kind] * n
    closed_months = [m for m in w.closes if w.closes[m] <= extract and m >= spec["first_kpi_month"]]
    used = set()
    for kind in templates:
        for _attempt in range(200):
            m = rng.choice(closed_months)
            ms, me = month_start_end(m)
            d = me - timedelta(days=rng.randint(0, 6))
            r, c = rng.choice(regions), rng.choice(classes)
            key = (r, c, d)
            if key in used or key not in nominal:
                continue
            C = closes[m]
            if kind in ("dc_after_close", "dc_before_close") and nominal[key]["IS"] >= C - timedelta(hours=50):
                continue  # the flawed IS must be published well before a correction placed around the close
            used.add(key)
            if kind == "withdrawn_after_close":
                pub = safe(C - timedelta(hours=rng.uniform(6, 30)))
                wd_at = safe(C + timedelta(hours=rng.uniform(1, 20)))
                nominal[key]["IS"] = pub
                modes[key + ("IS",)] = {"mode": "withdraw", "withdraw_at": wd_at,
                                        "rerun_at": safe(local_rand(add_wd(wd_at.date(), rng.randint(1, 4)), 10, 16))}
            elif kind == "gap_at_close":
                pub = safe(C - timedelta(hours=rng.uniform(20, 60)))
                wd_at = safe(C - timedelta(hours=rng.uniform(2, 15)))
                nominal[key]["IS"] = pub
                modes[key + ("IS",)] = {"mode": "withdraw", "withdraw_at": wd_at,
                                        "rerun_at": safe(local_rand(add_wd(C.date(), rng.randint(1, 5)), 10, 16))}
            elif kind == "is_after_close":
                nominal[key]["IS"] = safe(C + timedelta(hours=rng.uniform(2, 72)))
                modes[key + ("IS",)] = {"mode": "plain"}
            elif kind in ("dc_after_close", "dc_before_close"):
                pub = nominal[key]["IS"]
                if kind == "dc_after_close":
                    corr = safe(C + timedelta(hours=rng.uniform(1, 46)))
                else:
                    corr = safe(C - timedelta(hours=rng.uniform(1, 46)))
                    if corr <= pub + timedelta(hours=1):
                        pub = safe(corr - timedelta(hours=rng.uniform(26, 90)))
                        nominal[key]["IS"] = pub
                sign = rng.choice([-1, 1])
                modes[key + ("IS",)] = {"mode": "flawed", "correct_at": corr,
                                        "delta": sign * rng.uniform(*DC_DELTA)}
            break
    # guarantee R1/R2 publications do not precede the (possibly moved) IS publication
    for key in used:
        p = nominal[key]
        for rt in ("R1", "R2", "RF", "DF"):
            if rt in p and p[rt] <= p["IS"] + timedelta(days=3):
                p[rt] = safe(p["IS"] + timedelta(days=rng.randint(4, 9), seconds=rng.randint(0, 20000)))

    # withdrawals
    for key, pubs in nominal.items():
        for rt in pubs:
            if rt == "EST" or key + (rt,) in modes:
                continue
            if rng.random() < st["withdraw"]:
                wd_at = safe(pubs[rt] + notice_delay(rng))
                modes[key + (rt,)] = {"mode": "withdraw", "withdraw_at": wd_at,
                                      "rerun_at": safe(local_rand(add_wd(wd_at.date(), rng.randint(1, 6)), 10, 16))}

    # data-correction batches
    for rt, share in st["dc"].items():
        for r in regions:
            for c in classes:
                dates = sorted(d for (rr, cc, d) in nominal if rr == r and cc == c and rt in nominal[(r, c, d)])
                i = 0
                while i < len(dates):
                    if rng.random() < share / 6.5:
                        L = rng.randint(3, 10)
                        batch = [d for d in dates[i:i + L] if (r, c, d, rt) not in modes]
                        i += L
                        if not batch:
                            continue
                        last_pub = max(nominal[(r, c, d)][rt] for d in batch)
                        corr_day = last_pub.date() + timedelta(days=rng.randint(2, 40))
                        corr = safe(local_rand(corr_day, 9, 17))
                        if corr <= last_pub + timedelta(hours=1):
                            corr = safe(last_pub + timedelta(hours=rng.uniform(2, 30)))
                        delta = rng.choice([-1, 1]) * rng.uniform(*DC_DELTA)
                        for d in batch:
                            modes[(r, c, d, rt)] = {"mode": "flawed", "correct_at": corr,
                                                    "delta": delta * rng.uniform(0.85, 1.15)}
                    else:
                        i += 1

    # ---------------------------------------------------------------- settlement: build run chains
    runs = []  # dicts
    for key in sorted(nominal):
        r, c, d = key
        cp = spec["classes"][c]
        V = vtrue[key]
        a = anom[r][d]
        normal = {"EST": V * (1 + rng.gauss(0, 0.025))}
        for rt in ("IS", "R1", "R2", "RF"):
            s = cp["est_share"] * EST_SHARE_FACTOR[rt]
            normal[rt] = V * (1 + s * kappa * a + rng.gauss(0, 0.012 * s))
        normal["DF"] = normal["RF"] * (1 + rng.gauss(0, 0.02))
        for rt in RUN_TYPES:
            if rt not in nominal[key]:
                continue
            pub = nominal[key][rt]
            mode = modes.get(key + (rt,), {"mode": "plain"})
            chain = build_chain(rng, spec, key, rt, pub, normal[rt], mode, safe, local_rand)
            runs.extend(chain)
    # cut at the extract instant
    kept = []
    for run in runs:
        if run["published_at"] > extract:
            continue
        run["events"] = sorted([ev for ev in run["events"] if ev[2] <= extract], key=lambda ev: ev[2])
        kept.append(run)
    kept.sort(key=lambda x: (x["published_at"], x["region"], x["class"], x["delivery_date"], x["run_type"]))
    for i, run in enumerate(kept, 1):
        run["run_id"] = f"SR{i:07d}"
    for run in kept:
        rep = run.get("replaces")
        run["replaces_run_id"] = rep["run_id"] if rep is not None and "run_id" in rep and rep["published_at"] <= extract else None
    w.runs = kept
    validate_runs(kept)

    # ---------------------------------------------------------------- forecasts
    issues, values = generate_forecasts(spec, rng, vdet, anom, extract, safe)
    w.issues, w.values = issues, values
    return w


def notice_delay(rng) -> timedelta:
    """Time from a run's publication until the agent's withdrawal notice is received."""
    if rng.random() < 0.55:
        return timedelta(hours=rng.uniform(2, 40))
    return timedelta(days=rng.uniform(3, 45))


def validate_runs(runs) -> None:
    """Generator invariants the task relies on (fail the build if broken)."""
    by_id = {}
    per_key = defaultdict(list)
    for run in runs:
        by_id[id(run)] = run
        ev = run["events"]
        assert ev and ev[0][0] == "published" and ev[0][2] == run["published_at"], run
        assert all(e[2] >= run["published_at"] for e in ev), run
        assert all(ev[i][2] < ev[i + 1][2] for i in range(len(ev) - 1)), run
        rep = run.get("replaces")
        if rep is not None and run.get("replaces_run_id"):
            assert rep["published_at"] < run["published_at"], run
        if run["run_type"] == "IS":
            per_key[(run["region"], run["class"], run["delivery_date"])].append(run)
    for key, lst in per_key.items():
        instants = sorted({e[2] for run in lst for e in run["events"]})
        for t in instants:
            live = [run for run in lst if _status_at(run, t) == "published"]
            assert len(live) <= 1, (key, t, [r["run_id"] for r in live])


def build_chain(rng, spec, key, rt, pub, normal_value, mode, safe, local_rand):
    r, c, d = key
    st = spec["settlement"]

    def new_run(p, value, reason, replaces):
        return {"region": r, "class": c, "delivery_date": d, "run_type": rt, "reason": reason, "replaces": replaces,
                "published_at": p, "mwh": round(value, 3), "events": [("published", p, p)],
                "est_share": round(spec["classes"][c]["est_share"] * EST_SHARE_FACTOR.get(rt, 1.0), 4)
                if rt != "EST" else 1.0}

    chain = []
    if mode["mode"] == "plain":
        chain.append(new_run(pub, normal_value, "scheduled", None))
    elif mode["mode"] == "withdraw":
        sign = rng.choice([-1, 1])
        first = new_run(pub, normal_value * (1 + sign * rng.uniform(*GROSS_WITHDRAWN)), "scheduled", None)
        first["events"].append(("withdrawn", pub, mode["withdraw_at"]))
        chain.append(first)
        re = new_run(mode["rerun_at"], normal_value * (1 + rng.gauss(0, 0.001)), "withdrawal_rerun", first)
        chain.append(re)
    elif mode["mode"] == "flawed":
        first = new_run(pub, normal_value * (1 + mode["delta"]), "scheduled", None)
        first["events"].append(("superseded", mode["correct_at"], mode["correct_at"]))
        chain.append(first)
        corr = new_run(mode["correct_at"], normal_value * (1 + rng.gauss(0, 0.001)), "data_correction", first)
        chain.append(corr)
        prev = corr
        # correction chains and withdrawn corrections (rare; used by hidden extracts)
        if rng.random() < st.get("dc_chain", 0.0):
            corr["mwh"] = round(normal_value * (1 + rng.choice([-1, 1]) * rng.uniform(0.015, 0.04)), 3)
            t2 = safe(corr["published_at"] + timedelta(days=rng.randint(3, 25), seconds=rng.randint(0, 20000)))
            corr["events"].append(("superseded", t2, t2))
            corr2 = new_run(t2, normal_value * (1 + rng.gauss(0, 0.001)), "data_correction", corr)
            chain.append(corr2)
            prev = corr2
        if rng.random() < st.get("dc_withdrawn", 0.0):
            wt = safe(prev["published_at"] + notice_delay(rng))
            prev["events"].append(("withdrawn", prev["published_at"], wt))
            rerun = new_run(safe(local_rand(add_wd(wt.date(), rng.randint(1, 5)), 10, 16)),
                            normal_value * (1 + rng.gauss(0, 0.001)), "withdrawal_rerun", prev)
            chain.append(rerun)
    return chain


def generate_forecasts(spec, rng, vdet, anom, extract, safe):
    horizons = spec["horizons"]
    regions = list(spec["regions"])
    seed = spec["seed"]
    iss = spec["issuing"]
    kappa = spec["kappa"]
    issues, values = [], []
    first_run = min(D(m["first_run"]) for m in spec["models"])
    for mp in spec["models"]:
        model = mp["model"]
        for o in daterange(D(mp["first_run"]), extract.date()):
            gate = local_to_utc(o, 11, 0)
            plan = []  # (issued_at, kind, scope, factors)
            sched_fail = rng.random() < iss["sched_fail"]
            if not sched_fail:
                plan.append((local_to_utc(o, 6, rng.randint(0, 8), rng.randint(0, 59)), "scheduled", None, "base"))
            elif rng.random() >= iss["no_pregate"] / iss["sched_fail"]:
                plan.append((local_rand_min(rng, o, 7 + 10 / 60, 10 + 40 / 60), "reissue", None, "base"))
            if plan and rng.random() < iss["partial_pregate"]:
                plan.append((local_rand_min(rng, o, 7.5, 10 + 50 / 60), "reissue", rng.choice(regions), "pregate"))
            if rng.random() < iss["gate_miss"]:
                scope = rng.choice(regions) if rng.random() < iss["gate_miss_partial"] else None
                plan.append((local_rand_min(rng, o, 11 + 2 / 60, 11 + 58 / 60), "reissue", scope,
                             "gatemiss" if plan else "base"))
            if rng.random() < mp["auto_reissue"]:
                if rng.random() < mp.get("auto_pregate", 0.0):
                    plan.append((local_rand_min(rng, o, 10 + 20 / 60, 10 + 55 / 60), "auto_reissue", None, "auto"))
                else:
                    plan.append((local_rand_min(rng, o, 12 + 25 / 60, 12 + 55 / 60), "auto_reissue", None, "auto"))
            if rng.random() < mp["review_reissue"]:
                plan.append((local_rand_min(rng, o, 14, 18), "reissue", None, "review" if plan else "base"))
            plan.sort(key=lambda x: x[0])
            prev_t = None
            for n, (t, kind, scope, fac) in enumerate(plan):
                t = safe(t)
                if abs((t - gate).total_seconds()) < 90:
                    t += timedelta(seconds=181)
                if prev_t is not None and t <= prev_t:
                    t = prev_t + timedelta(seconds=37)
                prev_t = t
                if t > extract:
                    continue
                issue = {"model": model, "run_date": o, "issued_at": t, "kind": kind, "scope": scope, "n": n,
                         "note": ISSUE_NOTES[fac]}
                issues.append(issue)
                for r in (regions if scope is None else [scope]):
                    for h in range(1, horizons + 1):
                        tgt = o + timedelta(days=h)
                        struct = portfolio_structure(spec, tgt)
                        w_rng = keyed_rng(seed, "w", o, r, tgt)
                        winter = 1 + spec["winter_error"] * max(0.0, math.cos(2 * math.pi * (tgt.timetuple().tm_yday - 15) / 365.25))
                        wv = w_rng.gauss(0, (spec["weather_w0"] + spec["weather_wh"] * h) * winter)
                        for p in sorted(struct):
                            cls = [c for c in struct[p] if class_active(spec, c, tgt)]
                            if not cls:
                                continue
                            u_rng = keyed_rng(seed, "u", model, o, r, p, tgt)
                            u = u_rng.gauss(0, (mp["u0"] + mp["uh"] * h) * winter)
                            if fac == "base":
                                eps = mp["a"] * wv + u
                            elif fac == "pregate":
                                eps = mp["a"] * 0.9 * wv + 0.95 * u + keyed_rng(seed, "n", model, o, n, r, p, tgt).gauss(0, 0.003)
                            elif fac == "gatemiss":
                                eps = mp["a"] * 0.75 * wv + u
                            elif fac == "auto":
                                eps = mp["a"] * 0.5 * wv + 0.9 * u
                            else:  # review
                                eps = mp["a"] * 0.8 * wv + u
                            e_is = sum(vdet[(r, c, tgt)] * (1 + spec["classes"][c]["est_share"] * kappa * anom[r][tgt])
                                       for c in cls)
                            values.append((issue, r, p, tgt, round(e_is * (1 + eps), 3)))
    issues.sort(key=lambda x: (x["issued_at"], x["model"], x["scope"] or ""))
    for i, issue in enumerate(issues, 1):
        issue["issue_id"] = f"FI{i:06d}"
    return issues, values


ISSUE_NOTES = {"base": "", "pregate": "re-run after input data refresh", "gatemiss": "re-run after input data refresh",
               "auto": "automatic re-issue: 06Z weather update", "review": "re-run for forecast review"}


def local_rand_min(rng, d, h0, h1):
    secs = rng.randint(int(h0 * 3600), int(h1 * 3600))
    return local_to_utc(d, secs // 3600, (secs % 3600) // 60, secs % 60)


# ------------------------------------------------------------------------------------------------ database

SCHEMA = """
CREATE TABLE regions (region TEXT PRIMARY KEY, name TEXT NOT NULL);
CREATE TABLE settlement_classes (settlement_class TEXT PRIMARY KEY, description TEXT NOT NULL);
CREATE TABLE settlement_runs (
  run_id TEXT PRIMARY KEY, region TEXT NOT NULL, settlement_class TEXT NOT NULL, delivery_date TEXT NOT NULL,
  run_type TEXT NOT NULL, reason TEXT NOT NULL, replaces_run_id TEXT, published_at TEXT NOT NULL,
  status TEXT NOT NULL, status_effective_from TEXT NOT NULL);
CREATE TABLE settlement_volumes (run_id TEXT PRIMARY KEY, mwh REAL NOT NULL, estimated_share REAL NOT NULL,
  loaded_at TEXT NOT NULL);
CREATE TABLE run_status_history (run_id TEXT NOT NULL, status TEXT NOT NULL, effective_from TEXT NOT NULL,
  recorded_at TEXT NOT NULL);
CREATE TABLE models (model TEXT PRIMARY KEY, description TEXT NOT NULL, first_run_date TEXT NOT NULL,
  production_from TEXT, production_to TEXT);
CREATE TABLE forecast_issues (issue_id TEXT PRIMARY KEY, model TEXT NOT NULL, run_date TEXT NOT NULL,
  issued_at TEXT NOT NULL, issue_kind TEXT NOT NULL, scope_region TEXT, note TEXT NOT NULL);
CREATE TABLE forecast_values (issue_id TEXT NOT NULL, region TEXT NOT NULL, portfolio TEXT NOT NULL,
  target_date TEXT NOT NULL, mwh REAL NOT NULL);
CREATE TABLE portfolio_membership (portfolio TEXT NOT NULL, settlement_class TEXT NOT NULL,
  effective_from TEXT NOT NULL, effective_to TEXT);
CREATE TABLE dim_portfolio (portfolio TEXT NOT NULL, settlement_class TEXT NOT NULL, description TEXT NOT NULL);
CREATE TABLE kpi_close_log (kpi_month TEXT PRIMARY KEY, closed_at TEXT NOT NULL, signed_off_by TEXT NOT NULL);
CREATE INDEX ix_runs_key ON settlement_runs (region, settlement_class, delivery_date);
CREATE INDEX ix_hist_run ON run_status_history (run_id);
CREATE INDEX ix_fv_issue ON forecast_values (issue_id);
CREATE INDEX ix_fi_model_run ON forecast_issues (model, run_date);

CREATE VIEW settled_volumes_latest AS
SELECT r.region, r.settlement_class, r.delivery_date, r.run_id, r.run_type, r.published_at, v.mwh
FROM settlement_runs r JOIN settlement_volumes v ON v.run_id = r.run_id
WHERE r.status = 'published' AND r.run_type <> 'EST'
  AND NOT EXISTS (
    SELECT 1 FROM settlement_runs r2
    WHERE r2.region = r.region AND r2.settlement_class = r.settlement_class AND r2.delivery_date = r.delivery_date
      AND r2.status = 'published' AND r2.run_type <> 'EST' AND r2.published_at > r.published_at);

CREATE VIEW forecast_latest AS
SELECT i.model, i.run_date, i.issue_id, i.issued_at, v.region, v.portfolio, v.target_date, v.mwh
FROM forecast_issues i JOIN forecast_values v ON v.issue_id = i.issue_id
WHERE i.issued_at = (SELECT MAX(i2.issued_at) FROM forecast_issues i2
                     WHERE i2.model = i.model AND i2.run_date = i.run_date);
"""

REGION_NAMES = {"NORTH": "North", "MIDLANDS": "Midlands", "EAST": "East", "SOUTH": "South", "WEST": "West",
                "LONDON": "London"}
CLASS_DESC = {"DOM": "Domestic, non-half-hourly metered", "SME_NHH": "Small business, non-half-hourly metered",
              "SME_HH": "Small business, elective half-hourly metered", "IC_HH": "Industrial & commercial, half-hourly metered",
              "EV_HH": "EV charging hubs, half-hourly metered",
              "UMS": "Unmetered supplies (street lighting, signage)"}
PORTFOLIO_DESC = {"RESI": "Residential", "BUSINESS": "Business (all non-domestic)", "SME": "Small and medium business",
                  "IC": "Industrial & commercial", "EV": "EV charging"}
MIGRATION_LOAD = "2026-07-02T03:14:09Z"


def write_db(w: World, path: Path) -> None:
    spec = w.spec
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        path.unlink()
    con = sqlite3.connect(path)
    con.executescript(SCHEMA)
    con.executemany("INSERT INTO regions VALUES (?,?)", [(r, REGION_NAMES.get(r, r.title())) for r in spec["regions"]])
    con.executemany("INSERT INTO settlement_classes VALUES (?,?)", [(c, CLASS_DESC.get(c, c)) for c in spec["classes"]])
    mig = T(MIGRATION_LOAD.replace("Z", ""))
    run_rows, vol_rows, hist_rows = [], [], []
    for run in w.runs:
        status, sat, _rec = run["events"][-1]
        run_rows.append((run["run_id"], run["region"], run["class"], run["delivery_date"].isoformat(), run["run_type"],
                         run["reason"], run["replaces_run_id"], fmt_ts(run["published_at"]), status, fmt_ts(sat)))
        loaded = mig if run["published_at"] < mig else run["published_at"] + timedelta(minutes=7 + (hash_int(run["run_id"]) % 50))
        vol_rows.append((run["run_id"], run["mwh"], run["est_share"], fmt_ts(loaded)))
        for s, e, t in run["events"]:
            hist_rows.append((run["run_id"], s, fmt_ts(e), fmt_ts(t)))
    con.executemany("INSERT INTO settlement_runs VALUES (?,?,?,?,?,?,?,?,?,?)", run_rows)
    con.executemany("INSERT INTO settlement_volumes VALUES (?,?,?,?)", vol_rows)
    hist_rows.sort(key=lambda x: (x[3], x[0]))
    con.executemany("INSERT INTO run_status_history VALUES (?,?,?,?)", hist_rows)
    con.executemany("INSERT INTO models VALUES (?,?,?,?,?)",
                    [(m["model"], m["description"], m["first_run"], m["production_from"], m["production_to"])
                     for m in spec["models"]])
    con.executemany("INSERT INTO forecast_issues VALUES (?,?,?,?,?,?,?)",
                    [(i["issue_id"], i["model"], i["run_date"].isoformat(), fmt_ts(i["issued_at"]), i["kind"],
                      i["scope"], i["note"]) for i in w.issues])
    fv = [(i["issue_id"], r, p, t.isoformat(), v) for (i, r, p, t, v) in w.values]
    fv.sort()
    con.executemany("INSERT INTO forecast_values VALUES (?,?,?,?,?)", fv)
    memb = []
    structs = spec["portfolios"]
    spans = defaultdict(list)  # (p, c) -> list of [from, to]
    for i, (eff, struct) in enumerate(structs):
        nxt = D(structs[i + 1][0]) - timedelta(days=1) if i + 1 < len(structs) else None
        for p, cls in struct.items():
            for c in cls:
                sp = spans[(p, c)]
                if sp and sp[-1][1] is not None and sp[-1][1] + timedelta(days=1) == D(eff):
                    sp[-1][1] = nxt
                else:
                    sp.append([D(eff), nxt])
    for (p, c), sp in sorted(spans.items()):
        for a, b in sp:
            memb.append((p, c, a.isoformat(), b.isoformat() if b else None))
    con.executemany("INSERT INTO portfolio_membership VALUES (?,?,?,?)", memb)
    cur = structs[-1][1]
    con.executemany("INSERT INTO dim_portfolio VALUES (?,?,?)",
                    [(p, c, PORTFOLIO_DESC.get(p, p)) for p in sorted(cur) for c in cur[p]])
    signers = ["Head of Trading Analytics", "Trading Analytics Manager"]
    con.executemany("INSERT INTO kpi_close_log VALUES (?,?,?)",
                    [(m, fmt_ts(t), signers[i % 2]) for i, (m, t) in enumerate(sorted(w.closes.items()))])
    con.commit()
    con.execute("VACUUM")
    con.close()


def hash_int(s: str) -> int:
    return int(hashlib.sha256(s.encode()).hexdigest()[:8], 16)


DIGEST_TABLES = ["regions", "settlement_classes", "settlement_runs", "settlement_volumes", "run_status_history", "models",
                 "forecast_issues", "forecast_values", "portfolio_membership", "dim_portfolio", "kpi_close_log"]


def db_digest(path: Path) -> str:
    hh = hashlib.sha256()
    con = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    try:
        for t in DIGEST_TABLES:
            hh.update(t.encode())
            try:
                rows = con.execute(f"SELECT * FROM {t}").fetchall()
            except sqlite3.Error:
                hh.update(b"<missing>")
                continue
            for row in sorted(rows, key=lambda x: tuple("" if v is None else str(v) for v in x)):
                hh.update(repr(row).encode())
        views = con.execute("SELECT name, sql FROM sqlite_master WHERE type IN ('view','table') ORDER BY name").fetchall()
        hh.update(repr(views).encode())
    finally:
        con.close()
    return hh.hexdigest()


# ------------------------------------------------------------------------------------------------ generator-side evaluation
# Used only to write the historical reports of the visible extract (the retired Billing snapshot / locked-forecast
# notebook at each close, and the mart after the migration). Computed from the generator's own bookkeeping.


def _status_at(run, t):
    if run["published_at"] > t:
        return None
    s = None
    for st, _eff, rec in run["events"]:
        if rec <= t:
            s = st
    return s


def _index(w: World):
    if hasattr(w, "_idx"):
        return w._idx
    by_key = defaultdict(list)
    for run in w.runs:
        by_key[(run["region"], run["class"], run["delivery_date"])].append(run)
    vals = defaultdict(list)
    for (i, r, p, t, v) in w.values:
        vals[(i["model"], i["run_date"])].append((i, r, p, t, v))
    w._idx = (by_key, vals)
    return w._idx


def eval_legacy_at_close(w: World, month: str):
    """Pack as produced at the close of `month` from the charge-basis snapshot and the locked forecasts."""
    spec = w.spec
    C = w.closes[month]
    by_key, vals = _index(w)
    ms, me = month_start_end(month)
    rows = []
    for mp in spec["models"]:
        for o in daterange(ms - timedelta(days=spec["horizons"]), me):
            gate = local_to_utc(o, 11, 0)
            locked = {}
            for (i, r, p, t, v) in vals.get((mp["model"], o), []):
                if i["issued_at"] < gate and ms <= t <= me:
                    k = (r, p, t)
                    if k not in locked or i["issued_at"] > locked[k][0]:
                        locked[k] = (i["issued_at"], v)
            for (r, p, t), (_ia, fv) in locked.items():
                cls = [c for c in portfolio_structure(spec, t).get(p, []) if class_active(spec, c, t)]
                total, ok = 0.0, True
                for c in cls:
                    basis = [run for run in by_key.get((r, c, t), []) if run["run_type"] == "IS" and _status_at(run, C) == "published"]
                    if len(basis) != 1:
                        ok = False
                        break
                    total += basis[0]["mwh"]
                rows.append((mp["model"], p, r, t, (t - o).days, fv, total if ok else None))
    return rows


def eval_mart_at(w: World, t_eval: datetime, months: list):
    """The migrated mart's semantics, run with the warehouse as it stood at `t_eval`."""
    spec = w.spec
    by_key, vals = _index(w)
    struct_now = portfolio_structure(spec, t_eval.date())
    rows = []
    for mp in spec["models"]:
        run_dates = sorted({o for (m, o) in vals if m == mp["model"]})
        for o in run_dates:
            if ym(o) not in months:
                continue
            cands = [x for x in vals[(mp["model"], o)] if x[0]["issued_at"] <= t_eval]
            if not cands:
                continue
            latest = max(x[0]["issued_at"] for x in cands)
            for (i, r, p, t, v) in cands:
                if i["issued_at"] != latest:
                    continue
                total, n = 0.0, 0
                for c in struct_now.get(p, []):
                    live = [run for run in by_key.get((r, c, t), []) if run["run_type"] != "EST" and _status_at(run, t_eval) == "published"]
                    if live:
                        total += max(live, key=lambda x: x["published_at"])["mwh"]
                        n += 1
                if n:
                    rows.append((mp["model"], p, r, t, (t - o).days, v, total, o))
    return rows


def _wape(rows):
    s_abs = sum(abs(fv - av) for fv, av in rows)
    s_act = sum(av for _fv, av in rows)
    return s_abs / s_act if s_act else float("nan")


PACK_NOTES = {
    "2026-01": "Coverage: forecasts for MIDLANDS delivery days 19-30 January are not scored (settlement agent outage, "
               "see ops/settlement_incidents.md).",
}


def _pct(x):
    return f"{100 * x:.2f}%"


def write_artifacts(w: World, root: Path) -> dict:
    spec = w.spec
    mig = spec["migration_month"]
    months = sorted(w.closes)
    pack_rows = []
    stats = {"h2h_pack": {}, "mart_pack": {}}
    out = root / "reports/kpi_packs"
    out.mkdir(parents=True, exist_ok=True)
    signers = {m: ("Head of Trading Analytics", "Trading Analytics Manager")[i % 2] for i, m in enumerate(months)}
    for m in months:
        by = defaultdict(list)
        if m < mig:
            ex = eval_legacy_at_close(w, m)
            produced = "notebooks/kpi_pack_legacy.ipynb"
            paired = defaultdict(dict)
            for (model, p, r, t, h, fv, av) in ex:
                by[(model, p)].append((fv, av))
                if av is not None:
                    paired[(p, r, t, h)][model] = (fv, av)
            models = sorted({x[0] for x in ex})
            h2h_lines = []
            for i, a in enumerate(models):
                for b in models[i + 1:]:
                    both = [v for v in paired.values() if a in v and b in v]
                    if both:
                        wa, wb = _wape([v[a] for v in both]), _wape([v[b] for v in both])
                        stats["h2h_pack"][(m, a, b)] = (len(both), wa, wb)
                        h2h_lines.append(f"| {a} | {b} | {100 * wa:.1f}% | {100 * wb:.1f}% | {100 * (wb / wa - 1):+.1f}% |")
        else:
            ex = eval_mart_at(w, w.closes[m], [m])
            produced = "fcaccuracy mart (nightly run after close)"
            prod = {mp["model"]: (D(mp["production_from"]) if mp["production_from"] else date(1900, 1, 1),
                                  D(mp["production_to"]) if mp["production_to"] else date(2100, 1, 1)) for mp in spec["models"]}
            for (model, p, r, t, h, fv, av, o) in ex:
                by[(model, p)].append((fv, av))
            models = sorted({x[0] for x in ex})
            h2h_lines = []
            for i, a in enumerate(models):
                for b in models[i + 1:]:
                    ra = [(fv, av) for (mm, p, r, t, h, fv, av, o) in ex if mm == a and prod[a][0] <= o <= prod[a][1]]
                    rb = [(fv, av) for (mm, p, r, t, h, fv, av, o) in ex if mm == b and prod[b][0] <= o <= prod[b][1]]
                    if ra and rb:
                        wa, wb = _wape(ra), _wape(rb)
                        stats["mart_pack"][(m, a, b)] = (len(rb), wa, wb)
                        h2h_lines.append(f"| {a} | {b} | {100 * wa:.1f}% | {100 * wb:.1f}% | {100 * (wb / wa - 1):+.1f}% |")
        table = []
        for (model, p), lst in sorted(by.items()):
            scored = [(fv, av) for fv, av in lst if av is not None]
            row = {"kpi_month": m, "model": model, "portfolio": p,
                   "wape_pct": f"{100 * _wape(scored):.1f}" if scored else "", "signed_off_at": fmt_ts(w.closes[m]),
                   "produced_by": produced}
            pack_rows.append(row)
            table.append(f"| {model} | {p} | {row['wape_pct']}% |")
        if m in ("2026-01", "2026-05", mig, months[-1]):
            y, mo = int(m[:4]), int(m[5:])
            title = date(y, mo, 1).strftime("%B %Y")
            lines = [f"# Forecast accuracy pack: {title}", "",
                     f"- Delivery month: {m}",
                     f"- Signed off: {fmt_ts(w.closes[m])} ({signers[m]})",
                     f"- Produced by: {produced}", "",
                     "## WAPE by model and portfolio (all horizons, all regions)", "",
                     "| Model | Portfolio | WAPE |", "|---|---|---|", *table, "",
                     "## Head-to-head", "",
                     *(["| Model A | Model B | WAPE A | WAPE B | B vs A |", "|---|---|---|---|---|", *h2h_lines]
                       if h2h_lines else ["No comparison: no two models were in production in this month."]), ""]
            if m in PACK_NOTES:
                lines += [PACK_NOTES[m], ""]
            (out / f"{m}.md").write_text("\n".join(lines))
    with open(out / "pack_history.csv", "w", newline="") as fh:
        wr = csv.DictWriter(fh, fieldnames=list(pack_rows[0]))
        wr.writeheader()
        wr.writerows(pack_rows)
    stats["pack_rows"] = pack_rows

    # ops daily dashboard (August): latest D+1 forecast scored against the next-morning estimate
    by_key, vals = _index(w)
    struct_now = portfolio_structure(spec, w.extract.date())
    last_m = months[-1]
    ms, me = month_start_end(last_m)
    dash = []
    for mp in spec["models"]:
        for t in daterange(ms, me):
            o = t - timedelta(days=1)
            cands = vals.get((mp["model"], o), [])
            if not cands:
                continue
            latest = max(x[0]["issued_at"] for x in cands)
            pairs = []
            for (i, r, p, tt, v) in cands:
                if i["issued_at"] != latest or tt != t:
                    continue
                est = [run for c in struct_now.get(p, []) for run in by_key.get((r, c, t), []) if run["run_type"] == "EST"]
                if est:
                    pairs.append((v, sum(x["mwh"] for x in est)))
            if pairs:
                dash.append({"delivery_date": t.isoformat(), "model": mp["model"], "horizon": 1,
                             "wape_vs_estimate_pct": f"{100 * _wape(pairs):.2f}", "forecast_units": len(pairs)})
    (root / "reports/ops").mkdir(parents=True, exist_ok=True)
    with open(root / f"reports/ops/daily_accuracy_dashboard_{last_m}.csv", "w", newline="") as fh:
        wr = csv.DictWriter(fh, fieldnames=["delivery_date", "model", "horizon", "wape_vs_estimate_pct", "forecast_units"])
        wr.writeheader()
        wr.writerows(dash)
    return stats


def build(spec: dict, root: Path) -> dict:
    root = Path(root)
    w = generate(spec)
    write_db(w, root / "data/warehouse.sqlite")
    stats = {}
    if spec.get("artifacts"):
        stats = write_artifacts(w, root)
    return {"world": w, "stats": stats}


if __name__ == "__main__":
    target = Path(sys.argv[1] if len(sys.argv) > 1 else ".")
    res = build(copy.deepcopy(VISIBLE_SPEC), target)
    w = res["world"]
    print(f"runs={len(w.runs)} issues={len(w.issues)} values={len(w.values)} closes={len(w.closes)}")
