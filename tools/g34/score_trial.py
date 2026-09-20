"""Score one G34 Gemini baseline trial: integrity, reward, cost, and the produced numbers
measured against the frozen tolerance.  Pure inspection - runs no model and no container.

    python tools/g34/score_trial.py jobs/g34-gemini3flash-baseline-1
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2] / "candidates" / "g34-fleet-reliability-gate"
sys.path.insert(0, str(ROOT / "tests"))
import scenarios                                                   # noqa: E402

QUANT = ("unplanned_failure_rate_36m", "overhaul_rate_36m", "retirement_rate_36m",
         "still_original_assembly_36m", "assembly_failure_rate_36m")
TRUTH_KEY = {"unplanned_failure_rate_36m": "q1_crude_failure_36",
             "overhaul_rate_36m": "cif_overhaul_36",
             "retirement_rate_36m": "cif_retirement_36",
             "still_original_assembly_36m": "survival_36",
             "assembly_failure_rate_36m": "q2_net_failure_36"}
EXPECTED_GIT_CHECKSUM = "f14dd0c0dbcd763c"


def truth(fixture="visible"):
    aud = json.loads((Path(__file__).parent / "fixture_audit.json").read_text())
    return aud[fixture]["_truth"]


def find_trial(job: Path):
    for d in sorted(job.iterdir()):
        if d.is_dir() and (d / "result.json").exists():
            return d
    raise SystemExit("no trial directory under %s" % job)


def main(job_path):
    job = Path(job_path)
    trial = find_trial(job)
    res = json.loads((trial / "result.json").read_text())
    t = truth("visible")

    print("=" * 72)
    print("trial            :", res["trial_name"])
    print("task             :", res["task_name"])
    print("task_checksum    :", res["task_checksum"])
    print("agent            :", res["config"]["agent"]["name"],
          "/", res["config"]["agent"]["model_name"])
    print("exception_info   :", res.get("exception_info"))

    ar = res.get("agent_result") or {}
    vr = res.get("verifier_result") or {}
    reward = (vr.get("rewards") or {}).get("reward")
    print("-" * 72)
    print("reward           :", reward)
    print("cost_usd         :", ar.get("cost_usd"))
    print("tokens in/cache/out:", ar.get("n_input_tokens"), "/",
          ar.get("n_cache_tokens"), "/", ar.get("n_output_tokens"))
    ex = res.get("agent_execution") or {}
    print("agent window     :", ex.get("started_at"), "->", ex.get("finished_at"))

    # verifier detail
    ctrf = trial / "verifier" / "ctrf.json"
    if ctrf.exists():
        c = json.loads(ctrf.read_text())
        tests = c["results"]["tests"]
        failed = [x["name"] for x in tests if x["status"] != "passed"]
        print("-" * 72)
        print("checks passed    : %d / %d" % (len(tests) - len(failed), len(tests)))
        for f in failed:
            print("   FAILED:", f)

    # the numbers the agent actually produced
    out = trial / "artifacts" / "workspace" / "out" / "analysis_results.json"
    print("-" * 72)
    if not out.exists():
        print("analysis_results.json: NOT PRESENT in collected artifacts")
        return
    got = json.loads(out.read_text())
    print("produced numbers vs visible truth (error in tolerance units):")
    print("  %-32s %10s %10s %8s" % ("quantity", "produced", "truth", "err/tau"))
    for q in QUANT:
        v = got.get("aftermarket", {}).get(q, got.get("engineering", {}).get(q))
        if v is None:
            print("  %-32s %10s" % (q, "MISSING"))
            continue
        tv = t[TRUTH_KEY[q]]
        tau = scenarios.TOL_MULTIPLIER * scenarios.SE_REF["visible"][q]
        print("  %-32s %10.4f %10.4f %8.2f" % (q, v, tv, abs(v - tv) / tau))
    print("  %-32s %10s %10s" % ("recommendation", got.get("recommendation"), t["decision"]))
    s = sum(got.get("aftermarket", {}).get(q, 0.0) for q in QUANT[:4])
    print("  %-32s %10.6f" % ("conservation (should be 1)", s))


if __name__ == "__main__":
    main(sys.argv[1])
