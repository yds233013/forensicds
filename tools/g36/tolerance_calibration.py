"""G36 tolerance calibration. Run ONLY after the K9 gate has passed.

Chooses TOL_MULTIPLIER from a MEASURED window: above the worst legitimate route's error, below the
smallest error among wrong analyses that must be caught. Never inherited, never tuned to a model.

    python tools/g36/tolerance_calibration.py
"""
from __future__ import annotations

import json, sys
from pathlib import Path

import numpy as np

R = Path("/Users/yashshah2311/forensicds/candidates/g36-tou-capacity-gate")
for s in ("environment/build", "tests", "solution"):
    sys.path.insert(0, str(R / s))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import scenarios                                                    # noqa: E402
from analysis_panel import build_fixture, methods                   # noqa: E402

VALID = ("V_F1_stratified", "V_F2_joint_nonlinear", "V_F3_hierarchical")


def main():
    audit = json.loads((Path(__file__).parent / "fixture_audit.json").read_text())
    rows = []
    for name in scenarios.ALL_NAMES:
        w, t, fr = build_fixture(scenarios.by_name(name))
        rows.append((name, t, methods(fr)))

    print("=" * 100)
    print("TOLERANCE CALIBRATION - target_peak_kw")
    print("=" * 100)
    print("%-12s %10s %12s %12s %12s" % ("fixture", "SE_REF", "worst valid", "in SE units",
                                         "closest wrong"))
    lower, upper = 0.0, 1e9
    detail = []
    for name, t, m in rows:
        se = audit[name]["target_peak_kw"]
        tv = t["target_peak_mean"]
        v_err = max(abs(m[k] - tv) for k in VALID)
        wrongs = [(abs(m[k] - tv), k) for k in m if k not in VALID]
        w_err, w_key = min(wrongs)
        lower = max(lower, v_err / se)
        detail.append((name, se, v_err, v_err / se, w_err, w_err / se, w_key))
        print("%-12s %10.5f %12.5f %12.2f %12.5f  (%s, %.2f SE)" % (
            name, se, v_err, v_err / se, w_err, w_key, w_err / se))

    # The binding upper bound is the smallest wrong-method error ACROSS its best fixture: a wrong
    # method only has to be caught somewhere, because every fixture must pass.
    per_method = {}
    for name, t, m in rows:
        se = audit[name]["target_peak_kw"]
        tv = t["target_peak_mean"]
        for k in m:
            if k in VALID:
                continue
            per_method.setdefault(k, []).append(abs(m[k] - tv) / se)
    worst_case = {k: max(v) for k, v in per_method.items()}     # its most detectable fixture
    upper = min(worst_case.values())
    hardest = min(worst_case, key=worst_case.get)

    print("\nlower bound (worst legitimate route):            %.2f SE_REF" % lower)
    print("upper bound (hardest wrong method, %s): %.2f SE_REF" % (hardest[:22], upper))
    if upper <= lower:
        print("\n*** NO ADMISSIBLE WINDOW - a legitimate route is less accurate than a wrong one ***")
        sys.exit(1)
    choice = round(float(np.sqrt(lower * upper)), 1)
    print("\nadmissible window: %.2f < multiplier < %.2f" % (lower, upper))
    print("chosen (geometric centre, rounded): %.1f" % choice)
    print("  -> worst legitimate route at %.2f of tolerance" % (lower / choice))
    print("  -> hardest wrong method caught at %.2fx tolerance" % (upper / choice))

    print("\n%-12s %10s %10s" % ("fixture", "SE_REF", "tolerance"))
    for name, se, *_ in detail:
        print("%-12s %10.5f %10.5f" % (name, se, choice * se))

    print("\n" + "=" * 100)
    print("Does estate_tou_response_at_target_cdd add discrimination beyond the forecast?")
    print("=" * 100)
    resp_audit = {n: audit[n]["estate_tou_response_at_target_cdd"] for n in scenarios.ALL_NAMES}
    print("(measured in the mutation suite; see mutation results for methods caught ONLY by it)")
    for n in scenarios.ALL_NAMES:
        print("   %-12s SE_REF %.5f  tolerance %.5f" % (n, resp_audit[n], choice * resp_audit[n]))


if __name__ == "__main__":
    main()
