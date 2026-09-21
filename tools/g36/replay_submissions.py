"""Forensic replay: run each baseline trial's SUBMITTED capacity_forecast package on every fixture.
Deterministic re-execution of frozen artefacts. No model call. Does not touch the candidate."""
from __future__ import annotations
import importlib, json, os, shutil, sys, tempfile
from pathlib import Path

ROOT = Path("/Users/yashshah2311/forensicds")
C = ROOT / "candidates/g36-tou-capacity-gate"
sys.path[:0] = [str(C / "environment/build"), str(C / "tests")]
import world, scenarios                                             # noqa: E402
A = json.loads((ROOT / "tools/g36/fixture_audit.json").read_text())
GATE = 3.057


def fixture_db(name, seed_offset=0):
    sp = scenarios.by_name(name)
    if seed_offset:
        sp["seed"] += seed_offset
    w = world.build(sp); t = world.truth(w)
    d = tempfile.mkdtemp(); os.makedirs(d + "/data")
    db = world.write_sqlite(w, d + "/data")
    cbar = t["target_cdd_mean"]; p = t["estate_shares"]
    hh = sum(p[i] * world.response_at(sp, i, cbar) for i in range(4))
    L = [world._load_expected(sp, i, cbar, False) for i in range(4)]
    lw = sum(p[i] * L[i] * world.response_at(sp, i, cbar) for i in range(4)) / sum(p[i] * L[i] for i in range(4))
    return db, t, hh, lw


def run_pkg(pkg_dir, db):
    tmp = Path(tempfile.mkdtemp())
    shutil.copytree(pkg_dir, tmp / "capacity_forecast")
    for m in [k for k in sys.modules if k.startswith("capacity_forecast")]:
        del sys.modules[m]
    sys.path.insert(0, str(tmp))
    try:
        cli = importlib.import_module("capacity_forecast.cli")
        out = tmp / "out"
        cli.analyse(Path(db), out)
        return json.loads((out / "analysis_results.json").read_text())
    finally:
        sys.path.remove(str(tmp))


def main():
    trials = {}
    for k in (1, 2, 3):
        tr = [d for d in (ROOT / f"jobs/g36-gemini3flash-baseline-{k}").iterdir() if d.is_dir()][0]
        trials[k] = tr / "artifacts/workspace/capacity_forecast"
    rows = []
    print("%-3s %-9s %9s %9s %6s | %8s %8s %8s %7s %7s | %s" % (
        "T", "fixture", "forecast", "truth", "f/tol", "resp", "hh_wt", "load_wt", "r/tol", "rL/tol", "decision"))
    for name in scenarios.ALL_NAMES:
        db, t, hh, lw = fixture_db(name)
        tf = 2.5 * A[name]["target_peak_kw"]; tr_ = 2.5 * A[name]["estate_tou_response_at_target_cdd"]
        for k, pkg in trials.items():
            g = run_pkg(pkg, db)
            f, r, dcs = g["target_peak_kw"], g["estate_tou_response_at_target_cdd"], g["procurement_decision"]
            fe, re_hh, re_lw = abs(f - t["target_peak_mean"]) / tf, abs(r - hh) / tr_, abs(r - lw) / tr_
            rows.append(dict(trial=k, fixture=name, forecast=f, truth=t["target_peak_mean"], f_tol=fe,
                             resp=r, hh=hh, lw=lw, r_tol_hh=re_hh, r_tol_lw=re_lw,
                             decision=dcs, truth_dec=t["decision"]))
            print("%-3d %-9s %9.4f %9.4f %6.2f | %8.4f %8.4f %8.4f %7.2f %7.2f | %s%s" % (
                k, name, f, t["target_peak_mean"], fe, r, hh, lw, re_hh, re_lw, dcs,
                "" if dcs == t["decision"] else " *WRONG*"))
    (ROOT / "research/g36/replay_results.json").write_text(json.dumps(rows, indent=1))
    print("\nwould each trial pass ALL checks?")
    for k in trials:
        rs = [r for r in rows if r["trial"] == k]
        cur = all(r["f_tol"] <= 1 and r["r_tol_hh"] <= 1 and r["decision"] == r["truth_dec"] for r in rs)
        alt = all(r["f_tol"] <= 1 and r["r_tol_lw"] <= 1 and r["decision"] == r["truth_dec"] for r in rs)
        fonly = all(r["f_tol"] <= 1 and r["decision"] == r["truth_dec"] for r in rs)
        print("  trial %d: frozen verifier %s | load-weighted response %s | forecast+decision only %s"
              % (k, "PASS" if cur else "fail", "PASS" if alt else "fail", "PASS" if fonly else "fail"))


if __name__ == "__main__":
    main()
