"""Reference standard errors per graded extract and quantity (research/dev tool; no model).

    python tools/g35/fixture_audit.py [redraws]

Writes tools/g35/fixture_audit.json and prints a table ready to paste into tests/scenarios.py.
"""
from __future__ import annotations

import copy
import json
import math
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2] / "candidates" / "g35-dispatch-priority-gate"
sys.path.insert(0, str(ROOT / "tests"))
sys.path.insert(0, str(ROOT / "environment" / "build"))
sys.path.insert(0, str(ROOT / "solution"))
import world, scenarios                                            # noqa: E402
from dispatch_experiment import estimate, load                     # noqa: E402

QUANT = scenarios.QUANT


def oracle_values(db):
    b = load.blocks(db)
    return {"direct_effect_50": estimate.direct_effect_50(b),
            "spillover_50": estimate.spillover_50(b),
            "policy_effect_full": estimate.policy_effect_full(b)}


def main(redraws=60):
    out = {}
    for name in scenarios.ALL_NAMES:
        base = scenarios.by_name(name)
        errs = {q: [] for q in QUANT}
        for k in range(redraws):
            sp = copy.deepcopy(base)
            sp["seed"] = base["seed"] + 10007 * (k + 1)
            w = world.build(sp)
            t = world.truth(w, n_mc=2)
            d = tempfile.mkdtemp()
            db = world.write_sqlite(w, d)
            o = oracle_values(db)
            for q in QUANT:
                errs[q].append(o[q] - t[q])
        out[name] = {q: math.sqrt(sum(e * e for e in errs[q]) / len(errs[q])) for q in QUANT}
        w = world.build(base)
        t = world.truth(w)
        out[name]["_truth"] = {k: (round(v, 6) if isinstance(v, float) else v) for k, v in t.items()}
        print(name, json.dumps({q: round(out[name][q], 6) for q in QUANT}),
              t["decision"], flush=True)
    Path(__file__).with_name("fixture_audit.json").write_text(json.dumps(out, indent=1) + "\n")

    print("\nSE_REF = {")
    for name in scenarios.ALL_NAMES:
        print("    %r: {" % name)
        for q in QUANT:
            print("        %r: %.8f," % (q, out[name][q]))
        print("    },")
    print("}")
    print("SE_REF_REDRAWS = %d" % redraws)


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 60)
