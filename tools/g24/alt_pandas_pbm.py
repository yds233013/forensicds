"""Independent correct G24 implementation (dev tool): pandas, vectorised decision grouping, position-transfer IPS.

Written without reference to the reference solution or variant_ope.py:
  - decisions: vectorised TTL grouping with pandas (cumulative group start per session/surface);
  - examination curve per device estimated from exploration click rates by slot;
  - estimator: item-in-slate marginal 5/m with a theta_target/theta_logged position transfer;
  - intervals: seeded paired bootstrap over exploration decisions.
Usage: copy over recs_eval/cli.py.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sqlite3

import numpy as np
import pandas as pd

VARIANT: dict = {}
SLOTS = 5
POLICIES = ("v6", "v7", "v7_pd")


def ttl_seconds() -> int:
    for line in Path("serving/config/serving.yaml").read_text().splitlines():
        if line.strip().startswith("ttl_seconds:"):
            return int(line.split(":", 1)[1])
    raise KeyError("ttl_seconds")


def decisions_frame(con, ttl):
    s = pd.read_sql_query("SELECT * FROM rec_serves", con)
    s["t"] = pd.to_datetime(s["served_at"]).astype("int64") // 10**9
    s = s.sort_values(["session_id", "surface", "t", "serve_id"]).reset_index(drop=True)
    # a group starts when the session/surface changes or the serve is beyond TTL of the group's start; iterate
    # within each session because group starts depend on earlier starts
    starts = np.zeros(len(s), bool)
    key = (s["session_id"] + "|" + s["surface"]).to_numpy()
    t = s["t"].to_numpy()
    start_t = None
    for i in range(len(s)):
        if i == 0 or key[i] != key[i - 1] or t[i] - start_t > ttl:
            starts[i] = True
            start_t = t[i]
    s["decision_idx"] = np.cumsum(starts) - 1
    first = s[starts].set_index("decision_idx")
    return s, first


def main(argv=None):
    ap = argparse.ArgumentParser(prog="recs_eval")
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("ope")
    r.add_argument("--logs", default="data/logs.sqlite")
    r.add_argument("--out", default="out/ope")
    a = ap.parse_args(argv)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(f"file:{Path(a.logs).resolve()}?mode=ro", uri=True)
    serves, dec = decisions_frame(con, ttl_seconds())
    clicks = pd.read_sql_query("SELECT serve_id, position FROM click_events", con)
    clicks = clicks.merge(serves[["serve_id", "decision_idx"]], on="serve_id")
    clicked = set(zip(clicks["decision_idx"], clicks["position"]))
    cand = pd.read_sql_query("SELECT * FROM rec_candidates", con)
    con.close()

    # decisions.csv
    rows = []
    for di, d in dec.iterrows():
        for k in range(1, SLOTS + 1):
            rows.append((d["serve_id"], d["stream"], d["device"], d["served_at"], k, d[f"slot_{k}"],
                         int((di, k) in clicked)))
    pd.DataFrame(rows, columns=["decision_id", "stream", "device", "decided_at", "position", "item_id",
                                "clicked"]).to_csv(out / "decisions.csv", index=False)

    # target slates from eligible candidates
    cand = cand.merge(serves[["serve_id", "decision_idx"]], on="serve_id")
    elig = cand[cand["filter_reason"].isna()]
    m = elig.groupby("decision_idx").size()
    tgt = {}
    srows = []
    for p in POLICIES:
        top = elig.sort_values(["decision_idx", f"score_{p}"], ascending=[True, False]).groupby("decision_idx").head(SLOTS)
        top = top.assign(position=top.groupby("decision_idx").cumcount() + 1)
        tgt[p] = {(r.decision_idx, r.item_id): r.position for r in top.itertuples()}
        for r in top.itertuples():
            srows.append((dec.loc[r.decision_idx, "serve_id"], p, r.position, r.item_id, r.decision_idx))
    sl = pd.DataFrame(srows, columns=["decision_id", "policy", "position", "item_id", "di"])
    sl.sort_values(["di", "policy", "position"]).drop(columns="di").to_csv(out / "target_slates.csv", index=False)

    # examination curves per device from the exploration stream
    ex = dec[(dec["stream"] == "explore_shuffle") & dec.index.isin(m.index)]
    theta = {}
    for dev, g in ex.groupby("device"):
        rate = np.array([sum((di, k) in clicked for di in g.index) / len(g) for k in range(1, SLOTS + 1)])
        theta[dev] = rate / rate[0]

    contrib = {p: np.zeros(len(ex)) for p in POLICIES}
    for i, (di, d) in enumerate(ex.iterrows()):
        th = theta[d["device"]]
        w = m.loc[di] / SLOTS
        for k in range(1, SLOTS + 1):
            if (di, k) not in clicked:
                continue
            item = d[f"slot_{k}"]
            for p in POLICIES:
                kt = tgt[p].get((di, item))
                if kt is not None:
                    contrib[p][i] += w * th[kt - 1] / th[k - 1]

    rng = np.random.default_rng(20240916)
    n = len(ex)
    boot_idx = rng.integers(0, n, size=(400, n))
    vals = []
    for p in POLICIES:
        est = contrib[p].mean()
        bs = contrib[p][boot_idx].mean(1)
        lift = (contrib[p] - contrib["v6"]).mean()
        lbs = (contrib[p] - contrib["v6"])[boot_idx].mean(1)
        se, lse = bs.std(ddof=1), lbs.std(ddof=1)
        vals.append((p, est, est - 1.96 * se, est + 1.96 * se, lift,
                     lift - 1.96 * lse if p != "v6" else 0.0, lift + 1.96 * lse if p != "v6" else 0.0))
    pv = pd.DataFrame(vals, columns=["policy", "value", "ci_low", "ci_high", "lift_vs_v6", "lift_ci_low",
                                     "lift_ci_high"])
    pv.to_csv(out / "policy_values.csv", index=False, float_format="%.12g")
    ok = pv[(pv["policy"] != "v6") & (pv["lift_ci_low"] > 0)]
    launch = ok.sort_values("value", ascending=False)["policy"].iloc[0] if len(ok) else "v6"
    (out / "launch.json").write_text(json.dumps({"launch": launch}, indent=2) + "\n")


if __name__ == "__main__":
    main()
