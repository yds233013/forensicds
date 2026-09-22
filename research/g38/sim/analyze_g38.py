"""G38 window analysis. Definitions PRE-REGISTERED here (identical in form to G37) before the 200-draw run finished:

z(m,f,q)        = |estimate - truth| / SE_REF(f,q);  SE_REF = RMSE of V2_state_space on fixture f
VALID_BOUND     = max over valid families + legitimate variants, fixtures, q in {q1, q2} of p99(z)
detect(m,f)     = max over q of p01(z)
WRONG_BOUND(m)  = second-largest detect(m,f) over fixtures (rejection on >= 2 fixtures)
WRONG_BOUND     = min over WRONG (not 'ambiguous') methods;  ambiguous methods are reported separately
ratio           = WRONG_BOUND / VALID_BOUND  (requirement >= 3)
Systematic bias and sampling SD are reported separately (bias_se, sd_se).
"""
from __future__ import annotations

import json, math, sys
from pathlib import Path

R = json.loads(Path(__file__).with_name(sys.argv[1] if len(sys.argv) > 1 else "g38_R1_supplier.json").read_text())
FX = list(R["fixtures"]); M = R["methods"]; Q = ("q1", "q2")
VK = ("valid", "legit")
vb = max((max(M[m]["fx"][f]["p99"][q] for q in Q), m, f) for m in M if M[m]["kind"] in VK for f in FX)
det = {m: {f: max(M[m]["fx"][f]["p01"][q] for q in Q) for f in FX} for m in M if M[m]["kind"] not in VK}
wb = {m: sorted(d.values(), reverse=True)[1] for m, d in det.items()}
wrong = [m for m in wb if M[m]["kind"] == "wrong"]
WBm = min(wrong, key=wb.get)
print("VALID families / legit variants  bias±sd (SE_REF units) per fixture, q1 | q2")
for m in M:
    if M[m]["kind"] in VK:
        print("  %-26s %s" % (m, "  ".join("%s:%+.2f±%.2f|%+.2f±%.2f" % (f[:8], M[m]["fx"][f]["bias_se"]["q1"], M[m]["fx"][f]["sd_se"]["q1"],
              M[m]["fx"][f]["bias_se"]["q2"], M[m]["fx"][f]["sd_se"]["q2"]) for f in FX)))
print("\nVALID_BOUND %.2f (%s on %s)   WRONG_BOUND %.2f (%s)   ratio %.2f" % (vb[0], vb[1], vb[2], wb[WBm], WBm, wb[WBm] / vb[0]))
print("\nWRONG / AMBIGUOUS: detect per fixture (p01 z), bias q1 in SE, decision-correct %")
for m in sorted(det, key=lambda k: wb[k]):
    print("  %-40s %-9s WB %6.2f | %s" % (m, M[m]["kind"], wb[m], " ".join(
        "%s:%5.1f(b%+5.1f,%3.0f%%)" % (f[:8], det[m][f], M[m]["fx"][f]["bias_se"]["q1"], 100 * M[m]["fx"][f]["decision_correct"]) for f in FX)))
print("\nFIXTURES")
for f in FX:
    v = R["fixtures"][f]
    print("  %-9s n_enr %.0f  Q1 truth %.1f [%.1f,%.1f]  |Q1-75| %.1f  SE_REF q1 %.1f q2 %.4f  Q2 %.3f  expand %.2f" % (
        f, v["n_enr_mean"], v["truth_q1_mean"], v["truth_q1_p05"], v["truth_q1_p95"], abs(v["truth_q1_mean"] - 75),
        v["se_ref"]["q1"], v["se_ref"]["q2"], v["truth_q2_mean"], v["expand_share"]))
Path(__file__).with_name(Path(sys.argv[1] if len(sys.argv) > 1 else "g38_R1_supplier.json").stem + "_window.json").write_text(json.dumps(
    {"VALID_BOUND": vb[0], "VALID_BOUND_from": vb[1:], "WRONG_BOUND": wb[WBm], "WRONG_BOUND_method": WBm,
     "ratio": wb[WBm] / vb[0], "detect": det, "wrong_bound": wb}, indent=1) + "\n")
