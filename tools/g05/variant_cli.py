"""Drop-in `sco_readout/cli.py` for the G05 mutation suite (dev tool; copied into a workspace by shortcuts.py).

VARIANT selects the estimator (research/g05/pilot/g05_estimators.py, copied alongside as sco_readout/_g05_estimators.py
and sco_readout/_g05_sim.py), panel mutations and overfits. Intervals come from a store bootstrap (B draws).
"""
from __future__ import annotations

import argparse
import json
import sqlite3
from pathlib import Path

import numpy as np
import pandas as pd

VARIANT = {"method": "imp_format_week"}          # replaced by shortcuts.py

HURDLE = 0.025
FORMATS = ("Supercentre", "Market", "Neighbourhood")


def load(db: Path) -> dict:
    con = sqlite3.connect(f"file:{Path(db).resolve()}?mode=ro", uri=True)
    q = lambda s: pd.read_sql_query(s, con)
    t = dict(kpi=q("SELECT * FROM kpi_store_week"), stores=q("SELECT * FROM stores"),
             plan=q("SELECT * FROM rollout_plan"), go=q("SELECT store_id, event_date, kit FROM install_log WHERE event='go_live'"),
             closures=q("SELECT store_id, closure_date FROM store_closures"))
    con.close()
    return t


def panel(t: dict, v: dict) -> pd.DataFrame:
    p = t["kpi"].merge(t["plan"][["store_id", "wave", "planned_go_live"]], on="store_id", how="left")
    p = p.merge(t["go"][["store_id", "event_date"]], on="store_id", how="left")
    last = p["week_start"].max()
    if v.get("panel_planned"):
        p["go_live_week"] = p["planned_go_live"].where(p["planned_go_live"] <= last)
    else:
        p["go_live_week"] = p["event_date"]
    ev = (pd.to_datetime(p["week_start"]) - pd.to_datetime(p["go_live_week"])).dt.days // 7
    if v.get("panel_event_week1"):
        ev = ev + 1
    p["event_week"] = ev.astype("Int64")
    if v.get("panel_txns_comparable"):
        p["comparable"] = (p["customer_txns"] > 0).astype(int)
    else:
        c = t["closures"].copy()
        cd = pd.to_datetime(c["closure_date"])
        c["week_start"] = (cd - pd.to_timedelta(cd.dt.weekday, unit="D")).dt.strftime("%Y-%m-%d")
        closed = set(zip(c["store_id"], c["week_start"]))
        p["comparable"] = [0 if k in closed else 1 for k in zip(p["store_id"], p["week_start"])]
    p["log_net_sales"] = np.log(p["net_sales"])
    return p.sort_values(["store_id", "week_start"]).reset_index(drop=True)


def arrays(t: dict, p: pd.DataFrame) -> dict:
    stores = sorted(p["store_id"].unique())
    weeks = sorted(p["week_start"].unique())
    si = {s: i for i, s in enumerate(stores)}
    wi = {w: i for i, w in enumerate(weeks)}
    S, T = len(stores), len(weeks)
    r, c = p["store_id"].map(si).to_numpy(), p["week_start"].map(wi).to_numpy()
    y_s = np.zeros((S, T)); y_s[r, c] = np.log(p["net_sales"].to_numpy())
    y_n = np.zeros((S, T)); y_n[r, c] = np.log(p["customer_txns"].to_numpy())
    comp = np.zeros((S, T), bool)
    # estimation always uses the true comparable flag unless the variant says otherwise
    cc = t["closures"].copy()
    cd = pd.to_datetime(cc["closure_date"])
    cc["w"] = (cd - pd.to_timedelta(cd.dt.weekday, unit="D")).dt.strftime("%Y-%m-%d")
    closed = set(zip(cc["store_id"], cc["w"]))
    comp[r, c] = [k not in closed for k in zip(p["store_id"], p["week_start"])]
    st = t["stores"].set_index("store_id")
    fmt = np.array([FORMATS.index(st.loc[s, "format"]) for s in stores])
    sqft = np.array([st.loc[s, "sqft"] / 1000 for s in stores])
    go = t["go"].set_index("store_id")
    plan = t["plan"].set_index("store_id")
    live = np.array([s in go.index for s in stores])
    kit = np.array([0 if (go.loc[s, "kit"] if s in go.index else plan.loc[s, "planned_kit"]) == "full" else 1
                    for s in stores])
    wave = np.array([int(plan.loc[s, "wave"]) - 1 if s in go.index else 4 for s in stores])
    G = np.array([float(wi[go.loc[s, "event_date"]]) if s in go.index else np.inf for s in stores])
    planned = np.array([float(wi.get(plan.loc[s, "planned_go_live"], 10 ** 6)) if s in go.index else np.inf
                        for s in stores])
    return dict(spec={"rr_window": (12, 25), "gate": HURDLE}, S=S, T=T, fmt=fmt, kit=kit, wave=wave, G=G,
                planned=planned, comparable=comp, y_s=y_s, y_n=y_n, y_b=y_s - y_n, sqft=sqft)


def subset(a: dict, idx: np.ndarray) -> dict:
    b = dict(a)
    for k in ("fmt", "kit", "wave", "G", "planned", "sqft"):
        b[k] = a[k][idx]
    for k in ("comparable", "y_s", "y_n", "y_b"):
        b[k] = a[k][idx]
    b["S"] = len(idx)
    return b


def quantities(r: dict) -> dict:
    return {**{k[1:]: float(v) for k, v in r["wave"].items()}, "gate": float(r["gate"])}


def gate(warehouse: Path, out: Path) -> None:
    from sco_readout import _g05_estimators as E
    v = VARIANT
    t = load(warehouse)
    p = panel(t, v)
    a = arrays(t, p)
    fn = {**E.ACCEPTED, **E.WRONG, **E.UNDECIDED, **E.VARIANTS_OF_WRONG}[v["method"]]
    if v.get("hardcode_trends"):
        # overfit: detrend with this extract's format trends, then store + week effects only
        slopes = np.array(v["hardcode_trends"])[a["fmt"]]
        adj = slopes[:, None] * np.arange(a["T"])[None, :] / 52.0
        a["y_s"] = a["y_s"] - adj
        a["y_b"] = a["y_s"] - a["y_n"]
    point = quantities(fn(a))
    if v.get("hardcode_compact_effect") is not None:
        r = fn(a)
        rem = a["wave"] == 4
        share = float(np.mean(a["kit"][rem] == 0))
        point["gate"] = share * r["kit"]["full"] + (1 - share) * v["hardcode_compact_effect"]
    rng = np.random.default_rng(7)
    boots = []
    for _ in range(v.get("boot", 30)):
        idx = np.concatenate([rng.choice(np.flatnonzero(a["fmt"] == f), size=int((a["fmt"] == f).sum()))
                              for f in range(3)])
        boots.append(quantities(fn(subset(a, idx))))
    def ci(k):
        se = float(np.std([b[k] for b in boots], ddof=1))
        return {"estimate": point[k], "ci_low": point[k] - 1.96 * se, "ci_high": point[k] + 1.96 * se}
    readout = {"effect_by_wave": {w: ci(w) for w in ("1", "2", "3", "4")}, "gate_effect": ci("gate")}
    readout["decision"] = v.get("hardcode_decision") or ("continue" if point["gate"] >= HURDLE else "stop")
    out.mkdir(parents=True, exist_ok=True)
    p[["store_id", "week_start", "wave", "go_live_week", "event_week", "comparable", "log_net_sales"]].to_csv(
        out / "analysis_panel.csv", index=False)
    (out / "readout.json").write_text(json.dumps(readout, indent=2) + "\n")


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(prog="sco_readout")
    sub = ap.add_subparsers(dest="command", required=True)
    g = sub.add_parser("gate")
    g.add_argument("--warehouse", default="data/warehouse.sqlite")
    g.add_argument("--out", default="out")
    args = ap.parse_args(argv)
    gate(Path(args.warehouse), Path(args.out))


if __name__ == "__main__":
    main()
