#!/usr/bin/env python3
"""Build-time audit of the four frozen G05 extracts (dev tool; numpy).

1. SE_ref per extract and graded quantity: RMSE of the least efficient accepted estimator over Monte-Carlo noise
   redraws of the task generator with the design held fixed (tolerance = 3.5 x SE_ref).
2. On each frozen extract (its own noise seed): error / tolerance of every accepted and wrong analysis from the Phase-0
   panel (research/g05/pilot/g05_estimators.py), the gate margin in SE_ref, and pass/fail.
3. Writes SE_REF into candidates/g05-sco-rollout-gate/tests/scenarios.py and a JSON report.

4. Validation on N_REDRAWS fresh redraws (independent of the SE_ref redraws): pass rate of every accepted estimator
   and of every wrong analysis (values + decision) under the build tolerances.

usage: fixture_audit.py N_REDRAWS OUT.json
"""
from __future__ import annotations

import copy
import json
import math
import re
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
TASK = ROOT / "candidates/g05-sco-rollout-gate"
sys.path.insert(0, str(TASK / "tests"))
sys.path.insert(0, str(ROOT / "research/g05/pilot"))
import world as W  # noqa: E402
from scenarios import HIDDEN_SPECS  # noqa: E402
import g05_estimators as E  # noqa: E402

QUANTS = ["wave.1", "wave.2", "wave.3", "wave.4", "gate"]
TOL_SIGMA = 3.5


def adapt(world) -> dict:
    """Task-generator world -> the pilot estimators' array layout."""
    spec = world["spec"]
    stores = world["stores"]
    S, T = len(stores), spec["T"]
    y_s = np.empty((S, T)); y_n = np.empty((S, T)); comp = np.zeros((S, T), bool)
    for i, (sid, wk, sales, txns, sco, ph) in enumerate(world["kpi"]):
        s, t = divmod(i, T)
        y_s[s, t] = math.log(sales); y_n[s, t] = math.log(txns)
    for i, (sid, t, tau, c) in enumerate(world["tau"]):
        comp[i // T, t] = c
    fmt = np.array([W.FORMATS.index(s["format"]) for s in stores])
    kit = np.array([0 if s["kit"] == "full" else 1 for s in stores])
    wave = np.array([s["wave"] - 1 if s["G"] is not None else 4 for s in stores])
    G = np.array([np.inf if s["G"] is None else float(s["G"]) for s in stores])
    planned = np.array([float(s["planned"]) if s["G"] is not None else np.inf for s in stores])
    return dict(spec={"rr_window": spec["rr_window"], "gate": spec["gate"]}, S=S, T=T, fmt=fmt, kit=kit, wave=wave,
                G=G, planned=planned, comparable=comp, y_s=y_s, y_n=y_n, y_b=y_s - y_n,
                sqft=np.array([s["sqft"] / 1000 for s in stores]))


def flat(r) -> dict:
    return {**{f"wave.{k[1:]}": v for k, v in r["wave"].items()}, "gate": float(r["gate"])}


def truth_flat(world) -> dict:
    t = W.truth(world)
    return {**{f"wave.{k}": v for k, v in t["effect_by_wave"].items()}, "gate": t["gate_effect"],
            "decision": t["decision"], "pooled": t["pooled_installed"]}


def main(n_redraws: int, out: Path) -> int:
    specs = [W.VISIBLE_SPEC] + HIDDEN_SPECS
    report, se_ref, ok = {}, {}, True
    for spec in specs:
        name = spec["name"]
        t0 = time.time()
        errs = {m: {q: [] for q in QUANTS} for m in E.ACCEPTED}
        for r in range(n_redraws):
            sp = copy.deepcopy(spec)
            sp["noise_seed"] = spec["seed"] + 1000 + 7919 * r
            wd = W.build_world(sp)
            tr = truth_flat(wd)
            a = adapt(wd)
            for m, fn in E.ACCEPTED.items():
                est = flat(fn(a))
                for q in QUANTS:
                    errs[m][q].append(est[q] - tr[q])
        se_ref[name] = {}
        for q in QUANTS:
            rm = {m: float(np.sqrt(np.mean(np.square(errs[m][q])))) for m in E.ACCEPTED}
            se_ref[name][q] = max(rm.values())
        tol = {q: TOL_SIGMA * se_ref[name][q] for q in QUANTS}
        panels = (("accepted", E.ACCEPTED), ("wrong", E.WRONG), ("wrong", E.UNDECIDED), ("wrong", E.VARIANTS_OF_WRONG))
        def grade(a, tr):
            out = {}
            for kind, panel in panels:
                for m, fn in panel.items():
                    est = flat(fn(a))
                    ratios = {q: round(abs(est[q] - tr[q]) / tol[q], 2) for q in QUANTS}
                    dec = "continue" if est["gate"] >= spec["gate"] else "stop"
                    out[m] = {"kind": kind, "ratios": ratios, "decision": dec,
                              "passes_values_and_decision": max(ratios.values()) <= 1 and dec == tr["decision"]}
            return out
        wd = W.build_world(spec)
        tr = truth_flat(wd)
        rows = grade(adapt(wd), tr)
        for m, x in rows.items():
            if x["kind"] == "accepted" and not x["passes_values_and_decision"]:
                ok = False
        passes = {m: 0 for m in rows}
        worst = {m: 0.0 for m in rows}
        for r in range(n_redraws):
            sp = copy.deepcopy(spec)
            sp["noise_seed"] = spec["seed"] + 500000 + 104729 * r        # disjoint from the SE_ref redraws
            wv = W.build_world(sp)
            g = grade(adapt(wv), truth_flat(wv))
            for m, x in g.items():
                passes[m] += x["passes_values_and_decision"]
                worst[m] = max(worst[m], max(x["ratios"].values()))
        for m in rows:
            rows[m]["validation_pass_rate"] = f"{passes[m]}/{n_redraws}"
            rows[m]["validation_worst_ratio"] = round(worst[m], 2)
        margin = (tr["gate"] - spec["gate"]) / se_ref[name]["gate"]
        if abs(margin) < 3:
            ok = False
        report[name] = {"n_redraws_se_ref": n_redraws, "n_redraws_validation": n_redraws,
                        "truth": {k: (round(v, 5) if isinstance(v, float) else v) for k, v in tr.items()},
                        "se_ref": {q: round(v, 6) for q, v in se_ref[name].items()},
                        "gate_margin_se": round(margin, 2), "methods": rows}
        print(name, f"{time.time() - t0:.0f}s", "truth gate", round(tr["gate"], 4), tr["decision"],
              "margin", round(margin, 1), "se_ref", {q: round(v, 4) for q, v in se_ref[name].items()}, flush=True)
    out.write_text(json.dumps(report, indent=1) + "\n")
    sc = TASK / "tests/scenarios.py"
    body = f"SE_REF_REDRAWS = {n_redraws}\nSE_REF = " + json.dumps({n: {q: round(v, 6) for q, v in d.items()} for n, d in se_ref.items()},
                                    indent=4) + "\n"
    text = re.sub(r"(SE_REF_REDRAWS = \d+\n)?SE_REF = .*\Z", body, sc.read_text(), flags=re.S)
    sc.write_text(text)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(int(sys.argv[1]), Path(sys.argv[2])))
