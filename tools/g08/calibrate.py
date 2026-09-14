#!/usr/bin/env python3
"""Dev: calibrate the G08 world. Builds an extract, checks the reference against the correct variant and against the
generator's bookkeeping, and measures how each natural wrong repair changes examples and headline numbers.

usage: calibrate.py [--spec visible|hidden_a|hidden_b|hidden_c] [--dir DIR] [--variants all|none|name,...]
"""
from __future__ import annotations

import argparse
import copy
import importlib
import json
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
TASK = HERE.parents[1] / "candidates/g08-forecast-accuracy-vintages"
sys.path.insert(0, str(TASK / "tests"))
sys.path.insert(0, str(HERE))

import reference  # noqa: E402
import variant_mart  # noqa: E402
import world  # noqa: E402

WRONG = {
    "W1_latest_current": {"actual": "latest_current"},
    "W2_est_first": {"actual": "est_first"},
    "W3_is_current_status": {"actual": "is_current_status"},
    "W4_is_scheduled": {"actual": "is_scheduled"},
    "W5_latest_any_at_close": {"actual": "latest_any_at_close"},
    "W6_dc_any_type": {"actual": "dc_any_type"},
    "W7_pub_le_close_current_status": {"actual": "is_pub_le_close_current_status"},
    "S5_latest_is_published_by_close": {"actual": "is_latest_published_by_close"},
    "W8b_status_by_effective_time": {"actual": "status_by_effective_time"},
    "W9_is_at_asof": {"actual": "is_at_asof"},
    "W10_utc_gate": {"gate": "utc"},
    "W11_issue_grain": {"lock_grain": "issue"},
    "W12_latest_issue": {"gate": "none"},
    "W13_scheduled_only": {"gate": "scheduled_only"},
    "W14_current_mapping": {"mapping": "current"},
    "W15_mapping_run_date": {"mapping": "run_date"},
    "W16_kpi_month_run": {"kpi_month": "run"},
    "W17_unsettled_fallback": {"unsettled": "fallback_latest"},
    "W17b_unsettled_drop": {"unsettled": "drop"},
    "W19_unpaired": {"pairing": "production_periods"},
    "drop_revised": {"drop_revised": True},
    "mart_like": {"actual": "latest_current", "gate": "none", "lock_grain": "issue", "mapping": "current",
                  "kpi_month": "run", "pairing": "production_periods", "unsettled": "drop"},
}


def diff(ref, got):
    re, ge = ref["examples"], got["examples"]
    keys = set(re) | set(ge)
    n_key = len(set(re) ^ set(ge))
    n_val = 0
    for k in set(re) & set(ge):
        a, b = re[k], ge[k]
        if (a["issue_id"], a["status"], a["actual_run_ids"], a["kpi_month"]) != (b["issue_id"], b["status"], b["actual_run_ids"], b["kpi_month"]):
            n_val += 1
        elif a["actual_mwh"] is not None and abs(a["actual_mwh"] - b["actual_mwh"]) > 1e-6:
            n_val += 1
    return n_key, n_val, len(keys)


def headline(res):
    out = {}
    for (a, b), v in res["head_to_head"].items():
        out[f"{a}-{b}"] = (round(100 * v["wape_a"], 3), round(100 * v["wape_b"], 3), round(100 * v["relative_change"], 2), v["n_pairs"])
    return out


def generator_check(w, ref_res):
    """Charge basis at close from the generator's own run chains must equal the reference."""
    import collections
    by_key = collections.defaultdict(list)
    for run in w.runs:
        by_key[(run["region"], run["class"], run["delivery_date"].isoformat())].append(run)
    bad = 0
    for (model, region, portfolio, target, horizon), row in ref_res["examples"].items():
        if row["status"] != "scored":
            continue
        C = w.closes[row["kpi_month"]]
        for rid in row["actual_run_ids"].split(";"):
            run = next(r for lst in (by_key[(region, c, target)] for c in w.spec["classes"]) for r in lst if r["run_id"] == rid)
            if not (run["run_type"] == "IS" and world._status_at(run, C) == "published"):
                bad += 1
    return bad


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--spec", default="visible")
    ap.add_argument("--dir")
    ap.add_argument("--variants", default="all")
    ap.add_argument("--as-of")
    a = ap.parse_args()
    if a.spec == "visible":
        spec = copy.deepcopy(world.VISIBLE_SPEC)
    else:
        import scenarios
        spec = copy.deepcopy(next(s for s in scenarios.HIDDEN_SPECS if s["name"] == a.spec))
    root = Path(a.dir or f"/tmp/g08cal_{a.spec}")
    t0 = time.time()
    built = world.build(spec, root)
    w = built["world"]
    as_of = a.as_of or spec.get("as_of") or world.fmt_ts(w.extract)
    db = root / "data/warehouse.sqlite"
    print(f"[{a.spec}] built in {time.time() - t0:.1f}s: runs={len(w.runs)} issues={len(w.issues)} values={len(w.values)} as_of={as_of}")
    t0 = time.time()
    ref = reference.expected(db, as_of)
    print(f"reference in {time.time() - t0:.1f}s: examples={len(ref['examples'])} closed={ref['closed_months'][0]}..{ref['closed_months'][-1]}")
    uns = sum(1 for r in ref["examples"].values() if r["status"] == "unsettled")
    print(f"unsettled examples={uns}; generator consistency mismatches={generator_check(w, ref)}")
    print("reference head-to-head:", headline(ref))
    importlib.reload(variant_mart)
    variant_mart.VARIANT = {}
    corr = variant_mart.compute(db, as_of)
    print("correct variant diff vs reference (key, value, total):", diff(ref, corr), headline(corr) == headline(ref))
    if a.variants == "none":
        return
    names = list(WRONG) if a.variants == "all" else a.variants.split(",")
    for name in names:
        variant_mart.VARIANT = WRONG[name]
        res = variant_mart.compute(db, as_of)
        print(f"{name:34} diff={diff(ref, res)}  h2h={headline(res)}")
    if built["stats"]:
        st = built["stats"]
        print("pack h2h (n, v3, v4):", {k: (v[0], round(100 * v[1], 2), round(100 * v[2], 2), round(100 * (v[2] / v[1] - 1), 1)) for k, v in st["h2h_pack"].items()})



if __name__ == "__main__":
    main()
