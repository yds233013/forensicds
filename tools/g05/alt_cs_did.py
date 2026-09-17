"""Independent correct implementation (drop-in `sco_readout/cli.py`): long-format pandas 2x2 comparisons.

For every live store s and run-rate week t (weeks 13-26 after go-live, comparable weeks only):
    effect_st = [y_st - mean(y_s over comparable weeks go-live-10 .. go-live-3)]
              - mean over same-format stores not live by t and comparable at t of
                [y_ct - mean(y_c over its comparable weeks in the same base window)]
Store effects -> wave means; kit-version means reweighted to the kit mix of stores not yet installed.
Intervals: store bootstrap within format (seeded), recomputing store effects from resampled control pools.
"""
from __future__ import annotations

import argparse
import json
import sqlite3
from pathlib import Path

import numpy as np
import pandas as pd

HURDLE = 0.025
B = 60


def read(db):
    con = sqlite3.connect(f"file:{Path(db).resolve()}?mode=ro", uri=True)
    q = lambda s: pd.read_sql_query(s, con)
    kpi = q("SELECT store_id, week_start, net_sales FROM kpi_store_week")
    stores = q("SELECT store_id, format FROM stores")
    plan = q("SELECT store_id, wave, planned_kit FROM rollout_plan")
    go = q("SELECT store_id, event_date AS go_live_week, kit FROM install_log WHERE event = 'go_live'")
    clo = q("SELECT store_id, closure_date FROM store_closures")
    con.close()
    return kpi, stores, plan, go, clo


def build_panel(kpi, plan, go, clo):
    p = kpi.merge(plan[["store_id", "wave"]], on="store_id").merge(go[["store_id", "go_live_week"]], on="store_id",
                                                                   how="left")
    p["event_week"] = ((pd.to_datetime(p.week_start) - pd.to_datetime(p.go_live_week)).dt.days // 7).astype("Int64")
    d = pd.to_datetime(clo.closure_date)
    clo = clo.assign(week_start=(d - pd.to_timedelta(d.dt.dayofweek, unit="D")).dt.strftime("%Y-%m-%d"))
    bad = clo[["store_id", "week_start"]].drop_duplicates().assign(closed=1)
    p = p.merge(bad, on=["store_id", "week_start"], how="left")
    p["comparable"] = (p.closed.isna()).astype(int)
    p["log_net_sales"] = np.log(p.net_sales)
    return p.drop(columns="closed").sort_values(["store_id", "week_start"]).reset_index(drop=True)


def store_effects(p, fmt_of, weights):
    """Returns Series store_id -> run-rate effect for live stores (wide arrays; weights = bootstrap multiplicities)."""
    Y = p.pivot(index="store_id", columns="week_start", values="log_net_sales")
    C = p.pivot(index="store_id", columns="week_start", values="comparable").to_numpy().astype(bool)
    ids = Y.index.to_numpy()
    weeks = list(Y.columns)
    y = Y.to_numpy()
    widx = {w: i for i, w in enumerate(weeks)}
    gl = p.drop_duplicates("store_id").set_index("store_id").go_live_week.reindex(ids)
    G = np.array([widx[d] if isinstance(d, str) else np.inf for d in gl])
    fmts = np.array([fmt_of[s] for s in ids])
    wts = weights.reindex(ids).fillna(0.0).to_numpy()
    yc = np.where(C, y, np.nan)
    out = {}
    live = np.flatnonzero(np.isfinite(G))
    cohorts = sorted({(int(G[i]), fmts[i]) for i in live})
    for g, f in cohorts:
        tr = live[(G[live] == g) & (fmts[live] == f)]
        pool = np.flatnonzero(fmts == f)
        lo = max(g - 10, 0)
        base = np.nanmean(yc[:, lo:g - 2], axis=1) if g - 2 > lo else np.full(len(ids), np.nan)
        num = np.zeros(len(tr)); cnt = np.zeros(len(tr))
        for k in range(12, 26):
            t = g + k
            if t >= len(weeks):
                continue
            ctrl = pool[(G[pool] > t) & C[pool, t] & ~np.isnan(base[pool])]
            wc = wts[ctrl]
            if wc.sum() == 0:
                continue
            cdiff = float(((y[ctrl, t] - base[ctrl]) * wc).sum() / wc.sum())
            ok = C[tr, t] & ~np.isnan(base[tr])
            num += np.where(ok, (y[tr, t] - base[tr]) - cdiff, 0.0)
            cnt += ok
        for i, s in enumerate(tr):
            if cnt[i] > 0:
                out[ids[s]] = num[i] / cnt[i]
    return pd.Series(out)


def summarise(theta, weights, wave_of, kit_of, remaining):
    w = weights.reindex(theta.index).fillna(0.0)
    res = {}
    for wave in ("1", "2", "3", "4"):
        m = theta.index[theta.index.map(lambda s: str(wave_of[s]) == wave)]
        res[wave] = float((theta[m] * w[m]).sum() / w[m].sum())
    kits = {}
    for k in ("full", "compact"):
        m = theta.index[theta.index.map(lambda s: kit_of[s] == k)]
        kits[k] = float((theta[m] * w[m]).sum() / w[m].sum())
    share = float(np.mean([kit_of[s] == "full" for s in remaining]))
    res["gate"] = share * kits["full"] + (1 - share) * kits["compact"]
    return res


def gate(warehouse, out):
    kpi, stores, plan, go, clo = read(warehouse)
    p = build_panel(kpi, plan, go, clo)
    fmt_of = dict(zip(stores.store_id, stores.format))
    wave_of = dict(zip(plan.store_id, plan.wave))
    kit_of = {**dict(zip(plan.store_id, plan.planned_kit)), **dict(zip(go.store_id, go.kit))}
    remaining = [s for s in stores.store_id if s not in set(go.store_id)]
    ones = pd.Series(1.0, index=stores.store_id)
    point = summarise(store_effects(p, fmt_of, ones), ones, wave_of, kit_of, remaining)
    rng = np.random.default_rng(99)
    draws = []
    for _ in range(B):
        wts = pd.Series(0.0, index=stores.store_id)
        for f in sorted(set(fmt_of.values())):
            ids = [s for s in stores.store_id if fmt_of[s] == f]
            for s in rng.choice(ids, size=len(ids)):
                wts[s] += 1
        draws.append(summarise(store_effects(p, fmt_of, wts), wts, wave_of, kit_of, remaining))
    def ci(k):
        se = float(np.std([d[k] for d in draws], ddof=1))
        return {"estimate": point[k], "ci_low": point[k] - 1.96 * se, "ci_high": point[k] + 1.96 * se}
    out.mkdir(parents=True, exist_ok=True)
    p[["store_id", "week_start", "wave", "go_live_week", "event_week", "comparable", "log_net_sales"]].to_csv(
        out / "analysis_panel.csv", index=False)
    ro = {"effect_by_wave": {w: ci(w) for w in ("1", "2", "3", "4")}, "gate_effect": ci("gate")}
    ro["decision"] = "continue" if point["gate"] >= HURDLE else "stop"
    (out / "readout.json").write_text(json.dumps(ro, indent=2) + "\n")


def main(argv=None):
    ap = argparse.ArgumentParser(prog="sco_readout")
    sub = ap.add_subparsers(dest="command", required=True)
    g = sub.add_parser("gate")
    g.add_argument("--warehouse", default="data/warehouse.sqlite")
    g.add_argument("--out", default="out")
    a = ap.parse_args(argv)
    gate(Path(a.warehouse), Path(a.out))


if __name__ == "__main__":
    main()
