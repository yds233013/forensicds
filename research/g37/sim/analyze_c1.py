"""Analysis of c1_results.json with definitions PRE-REGISTERED here before the full run was inspected.

z(m, f, q)      = |estimate - truth| / SE_REF(f, q), SE_REF = RMSE of F1 over the redraws of fixture f
VALID_BOUND     = max over valid families + legitimate variants, fixtures, quantities of p99(z)
detect(m, f)    = max over quantities of p01(z)         (an error the method shows in >= 99 % of draws)
WRONG_BOUND(m)  = the SECOND largest detect(m, f) over fixtures (rejection on >= 2 fixtures)
WRONG_BOUND     = min over important wrong methods of WRONG_BOUND(m)
ratio           = WRONG_BOUND / VALID_BOUND, pre-registered requirement >= 3
multiplier M    = sqrt(VALID_BOUND * WRONG_BOUND) rounded down to 0.5 (fixed rule, same as G36's procedure)
rejected(m, f)  = detect(m, f) > M          (numeric; decision-only rejections reported separately)
decision compat = share of redraws with |truth - 1.33| > M * SE_REF(ppk)   (fixture realisation spread)
"""
from __future__ import annotations

import json, math, sys
from pathlib import Path

R = json.loads(Path(__file__).with_name(sys.argv[1] if len(sys.argv) > 1 else "c1_results.json").read_text())
FX = list(R["fixtures"])
Q = ("mean_post", "sd_post", "ppk_post", "sd_pre")
M = R["methods"]
VALIDK = ("valid", "legit_variant", "legitimate")

vb_rows = [(max(M[m]["fx"][f]["p99"][q] for q in Q), m, f) for m in M if M[m]["kind"] in VALIDK for f in FX]
VB = max(vb_rows)[0]
detect = {m: {f: max(M[m]["fx"][f]["p01"][q] for q in Q) for f in FX} for m in M if M[m]["kind"] not in VALIDK}
wb = {m: sorted(d.values(), reverse=True)[1] for m, d in detect.items()}
WB_m = min(wb, key=wb.get); WB = wb[WB_m]
mult = math.floor(math.sqrt(VB * WB) * 2) / 2 if WB > VB else float("nan")

print("VALID families: bias and SD in SE_REF units (per fixture: ppk_post / sd_post / mean_post / sd_pre)")
for m in M:
    if M[m]["kind"] in VALIDK:
        print("  %-30s %s" % (m, "  ".join("%s:%+.2f±%.2f/%+.2f/%+.2f/%+.2f" % (
            f[:8], M[m]["fx"][f]["bias_se"]["ppk_post"], M[m]["fx"][f]["sd_se"]["ppk_post"],
            M[m]["fx"][f]["bias_se"]["sd_post"], M[m]["fx"][f]["bias_se"]["mean_post"],
            M[m]["fx"][f]["bias_se"]["sd_pre"]) for f in FX)))
print("\nVALID_BOUND (p99) = %.2f   from %s on %s" % (VB, max(vb_rows)[1], max(vb_rows)[2]))
print("WRONG_BOUND (2nd-best fixture, p01) = %.2f   from %s" % (WB, WB_m))
print("ratio = %.2f   (pre-registered requirement >= 3)   ->  multiplier M = %s" % (WB / VB, mult))

print("\nWRONG / COUNTEREXAMPLE methods: detect(m,f) = max_q p01(z); '*' = rejected numerically at M; "
      "decision-correct rate in brackets")
for m in sorted(detect, key=lambda k: wb[k]):
    cells = []
    for f in FX:
        d = detect[m][f]; dc = M[m]["fx"][f]["decision_correct_rate"]
        cells.append("%s%6.1f%s[%3.0f%%]" % (f[:8] + ":", d, "*" if d > mult else " ", 100 * dc))
    nrej = sum(detect[m][f] > mult for f in FX)
    print("  %-48s %-20s WB=%6.2f rej %d/5  %s" % (m, M[m]["kind"], wb[m], nrej, " ".join(cells)))

print("\nFIXTURES: truth, dashboard, SE_REF(ppk), decision compatibility at M")
for f in FX:
    v = R["fixtures"][f]; tol = mult * v["se_ref"]["ppk_post"]
    print("  %-9s truthPpk %.3f [%.3f, %.3f]  |E truth - 1.33| %.3f  tol_ppk %.3f  dashboard %.3f  truth decision %s" % (
        f, v["truth_ppk_mean"], v["truth_ppk_min"], v["truth_ppk_max"], abs(v["truth_ppk_mean"] - 1.33), tol,
        v["raw_dashboard_ppk_mean"], v["truth_decision"]))
Path(__file__).with_name("c1_window.json").write_text(json.dumps(
    {"VALID_BOUND": VB, "WRONG_BOUND": WB, "WRONG_BOUND_method": WB_m, "ratio": WB / VB, "multiplier": mult,
     "detect": detect, "wrong_bound_by_method": wb}, indent=1) + "\n")
