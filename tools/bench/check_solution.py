"""Check a task's reference solution against its truth on every graded extract, without Docker.

Runs the solution package over each extract in a temporary workspace and compares every graded field against
`world.truth()` using the task's own `tests/tolerances.py`. Shared by the three prospective tasks.
"""
from __future__ import annotations

import argparse
import json
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[2]

# (task key, module invocation, db filename, readout comparison spec)
RUNNERS = {
    "quality": (["-m", "quality", "report"], "data/inspection.sqlite"),
    "mlops": (["-m", "mlops", "monitor"], "data/appointments.sqlite"),
    "service": (["-m", "service", "fill"], "data/service.sqlite"),
}


def compare(pkg, got, t, tol):
    """Return a list of mismatches. Kept per-task because the graded fields differ."""
    bad = []

    def near(label, g, w, lim):
        if g is None:
            bad.append(f"{label}: missing")
        elif abs(float(g) - float(w)) > lim:
            bad.append(f"{label}: {g} vs {w:.4f} (tol {lim})")

    if pkg == "quality":
        near("corrected", got.get("corrected_nonconforming_rate_pct"),
             t["corrected_nonconforming_rate_pct"], tol.RATE_CORRECTED_PP)
        near("baseline", got.get("baseline_nonconforming_rate_pct"),
             t["baseline_nonconforming_rate_pct"], tol.RATE_DIRECT_PP)
        near("reported", got.get("reported_nonconforming_rate_pct"),
             t["reported_nonconforming_rate_pct"], tol.RATE_DIRECT_PP)
        for m, w in t["conformance_reference_offset_um"].items():
            near(f"offset[{m}]", (got.get("conformance_reference_offset_um") or {}).get(m), w, tol.OFFSET_UM)
        for k, w in t["attribution_pp"].items():
            near(f"attrib[{k}]", (got.get("attribution_pp") or {}).get(k), w, tol.ATTRIBUTION_PP)
        if got.get("supplier_decision") != t["supplier_decision"]:
            bad.append(f"decision: {got.get('supplier_decision')} vs {t['supplier_decision']}")
    elif pkg == "mlops":
        near("monitored", got.get("monitored_auc"), t["deployed_auc_v31"], tol.AUC)
        near("floor", got.get("retention_floor_auc"), t["retention_floor_auc"], tol.AUC)
        for k, w in (("as_served", t["holdback_auc_v31_asof_features"]),
                     ("record_features_asof_window", t["holdback_auc_v31_repaired_feed"]),
                     ("feature_store_current", t["holdback_auc_v31_current_features"]),
                     ("candidate_v4", t["holdback_auc_v40"])):
            near(f"auc[{k}]", (got.get("auc_by_scoring") or {}).get(k), w, tol.AUC)
        for k, w in t["attribution_auc"].items():
            near(f"attrib[{k}]", (got.get("attribution_auc") or {}).get(k), w, tol.ATTRIBUTION)
        near("defect", got.get("feed_defect_share_pct"), t["feed_defect_share"], tol.DEFECT_SHARE_PP)
        near("effect", got.get("programme_effect_pp"), t["reminder_effect_pp"], tol.EFFECT_PP)
        pop = sorted((got.get("evaluation_population") or {}).get("clinic_ids") or [])
        if pop != sorted(t["monitoring_population"]):
            bad.append(f"population: {pop} vs {sorted(t['monitoring_population'])}")
        if got.get("decision") != t["decision"]:
            bad.append(f"decision: {got.get('decision')} vs {t['decision']}")
    else:
        near("contract", got.get("fill_rate_contract_pct"), t["fill_rate_contract_pct"], tol.RATE_PP)
        near("low", got.get("fill_rate_contract_low_pct"), t["fill_rate_contract_low_pct"], tol.RATE_PP)
        near("high", got.get("fill_rate_contract_high_pct"), t["fill_rate_contract_high_pct"], tol.RATE_PP)
        near("supplier", got.get("fill_rate_supplier_definition_pct"),
             t["fill_rate_supplier_definition_pct"], tol.RATE_PP)
        near("published", got.get("published_rate_pct"), t["published_rate_pct"], tol.RATE_PP)
        for k, w in t["bridge_pp"].items():
            near(f"bridge[{k}]", (got.get("bridge_pp") or {}).get(k), w, tol.BRIDGE_PP)
        for a, w in t["account_fill_pct"].items():
            near(f"account[{a}]", (got.get("account_fill_pct") or {}).get(a), w, tol.ACCOUNT_RATE_PP)
        near("tickets", got.get("returns_driven_ticket_share_pct"),
             t["returns_driven_ticket_share_pct"], tol.TICKET_SHARE_PP)
        for k in ("incumbent_verdict", "bonus_gate_met", "supplier_claim_payable", "governing_definition"):
            if got.get(k) != t[k]:
                bad.append(f"{k}: {got.get(k)} vs {t[k]}")
    return bad


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--task", required=True)
    ap.add_argument("--package", required=True)
    a = ap.parse_args()
    task = ROOT / a.task
    sys.path.insert(0, str(task / "tests"))
    import scenarios  # noqa: E402
    import tolerances  # noqa: E402
    import world  # noqa: E402

    argv, db = RUNNERS[a.package]
    ws = pathlib.Path(tempfile.mkdtemp())
    shutil.copytree(task / "environment/workspace", ws, dirs_exist_ok=True)
    for f in (task / "solution" / a.package).glob("*.py"):
        shutil.copy(f, ws / a.package / f.name)

    problems = []
    for n in scenarios.ALL_NAMES:
        w = world.build(scenarios.by_name(n))
        world.write_sqlite(w, str(ws))
        r = subprocess.run([sys.executable, *argv, "--db", db, "--out", "out"], cwd=str(ws),
                           env={**os.environ, "PYTHONPATH": str(ws)}, capture_output=True, text=True)
        if r.returncode != 0:
            problems.append(f"{n}: pipeline failed: {r.stderr[-400:]}")
            continue
        got = json.loads((ws / "out/readout.json").read_text())
        for m in compare(a.package, got, world.truth(w), tolerances):
            problems.append(f"{n}: {m}")
    shutil.rmtree(ws, ignore_errors=True)
    for p in problems:
        print("   " + p)
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
