"""Reference standard errors per graded extract and quantity (research/dev tool; no model)."""
from __future__ import annotations
import copy, json, sqlite3, sys, tempfile
from pathlib import Path
import numpy as np, pandas as pd

ROOT = Path(__file__).resolve().parents[2] / "candidates" / "g34-fleet-reliability-gate"
sys.path.insert(0, str(ROOT / "tests"))
sys.path.insert(0, str(ROOT / "solution"))
import world, scenarios                                            # noqa: E402
from fleet_reliability import history                              # noqa: E402

QUANT = ("unplanned_failure_rate_36m", "overhaul_rate_36m", "retirement_rate_36m",
         "still_original_assembly_36m", "assembly_failure_rate_36m")
TRUTH_KEY = {"unplanned_failure_rate_36m": "cif_failure_36", "overhaul_rate_36m": "cif_overhaul_36",
             "retirement_rate_36m": "cif_retirement_36", "still_original_assembly_36m": "survival_36",
             "assembly_failure_rate_36m": "q2_net_failure_36"}


def oracle_values(db):
    sys.path.insert(0, str(ROOT / "solution"))
    from fleet_reliability import estimate
    df = history.build(Path(db))
    s = estimate.outcome_shares(df, 36.0)
    return {"unplanned_failure_rate_36m": s["UNPL_FAIL"], "overhaul_rate_36m": s["PM_OVHL"],
            "retirement_rate_36m": s["ASSET_RET"], "still_original_assembly_36m": s["still_original"],
            "assembly_failure_rate_36m": estimate.assembly_life_failure_rate(df, 36.0)}


def main(redraws=100):
    out = {}
    for name in scenarios.ALL_NAMES:
        base = scenarios.by_name(name)
        errs = {q: [] for q in QUANT}
        for k in range(redraws):
            sp = copy.deepcopy(base); sp["seed"] = base["seed"] + 10007 * (k + 1)
            d = tempfile.mkdtemp(); w = world.build(sp); db = world.write_sqlite(w, d)
            t = world.truth(w); o = oracle_values(db)
            for q in QUANT:
                errs[q].append(o[q] - t[TRUTH_KEY[q]])
        out[name] = {q: float(np.sqrt(np.mean(np.square(errs[q])))) for q in QUANT}
        w = world.build(base); t = world.truth(w)
        out[name]["_truth"] = {k: (round(v, 6) if isinstance(v, float) else v) for k, v in t.items()}
        print(name, json.dumps({q: round(out[name][q], 5) for q in QUANT}), t["decision"], flush=True)
    Path(__file__).with_name("fixture_audit.json").write_text(json.dumps(out, indent=1) + "\n")


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 100)
