"""Score one G36 baseline trial from its job artefacts. Inspection only: no model, no container.
    python tools/g36/score_trial.py jobs/g36-gemini3flash-baseline-1
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

A = json.loads((Path(__file__).parent / "fixture_audit.json").read_text())
GATE = 3.057


def main(job):
    tr = [d for d in Path(job).iterdir() if d.is_dir() and (d / "result.json").exists()][0]
    r = json.loads((tr / "result.json").read_text())
    ar = r.get("agent_result") or {}
    vr = r.get("verifier_result") or {}
    ex = r.get("agent_execution") or {}
    print("trial          :", r["trial_name"])
    print("task_checksum  :", r["task_checksum"][:16])
    print("exception      :", r.get("exception_info"))
    print("reward         :", (vr.get("rewards") or {}).get("reward"))
    print("cost_usd       :", ar.get("cost_usd"))
    print("tokens in/cache/out:", ar.get("n_input_tokens"), ar.get("n_cache_tokens"), ar.get("n_output_tokens"))
    print("agent window   :", ex.get("started_at"), "->", ex.get("finished_at"))
    ctrf = tr / "verifier" / "ctrf.json"
    if ctrf.exists():
        tests = json.loads(ctrf.read_text())["results"]["tests"]
        bad = [t["name"] for t in tests if t["status"] != "passed"]
        print("checks passed  : %d / %d" % (len(tests) - len(bad), len(tests)))
        for b in bad:
            print("   FAILED:", b)
    so = tr / "verifier" / "test-stdout.txt"
    if so.exists():
        for line in so.read_text().splitlines():
            if re.search(r"reported|expected|error|tolerance", line) and len(line) < 400:
                print("   |", line.strip()[:260])
    traj = tr / "agent" / "trajectory.json"
    if traj.exists():
        t = json.loads(traj.read_text())
        n_tools = sum(len(s.get("tool_calls") or []) for s in t["steps"])
        print("steps / tool calls:", len(t["steps"]), "/", n_tools)
    out = tr / "artifacts" / "workspace" / "out" / "analysis_results.json"
    if not out.exists():
        print("analysis_results.json: NOT PRESENT"); return
    g = json.loads(out.read_text())
    v = A["visible"]["_truth"]
    tol_f = 2.5 * A["visible"]["target_peak_kw"]
    tol_r = 2.5 * A["visible"]["estate_tou_response_at_target_cdd"]
    fk, rk = g.get("target_peak_kw"), g.get("estate_tou_response_at_target_cdd")
    print("\nsubmitted (visible extract):")
    print("  target_peak_kw   %s  truth %.5f  err %s  tol %.5f" % (
        fk, v["target_peak_kw"], "%.5f" % (fk - v["target_peak_kw"]) if isinstance(fk, (int, float)) else "NA", tol_f))
    print("  estate_response  %s  truth %.5f  err %s  tol %.5f" % (
        rk, v["estate_tou_response_at_target_cdd"],
        "%.5f" % (rk - v["estate_tou_response_at_target_cdd"]) if isinstance(rk, (int, float)) else "NA", tol_r))
    print("  decision         %s  truth %s" % (g.get("procurement_decision"), A["visible"]["_decision"]))
    print("  target_cdd_mean  %s" % g.get("target_cdd_mean"))
    print("  n_households     %s" % g.get("n_households"))


if __name__ == "__main__":
    main(sys.argv[1])
