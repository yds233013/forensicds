"""v1.1 response tolerance: the SAME mechanical measured-window procedure as v1.
   lower = worst legitimate-family error / SE_REF over the frozen fixtures
   upper = min over wrong response analyses of (max over fixtures error / SE_REF)
   multiplier = round(sqrt(lower * upper), 1)
No discretion. Uses no saved baseline submission; the procedure never reads jobs/."""
import json, math
from pathlib import Path
R = Path("/Users/yashshah2311/forensicds")
audit = json.loads((R / "tools/g36_v11/fixture_audit.json").read_text())
val = json.loads((R / "research/g36/v1_1/response_validation.json").read_text())
Q = "estate_tou_response_at_target_cdd"
FAM = ["F1_stratified", "F2_joint_nonlinear", "F3_hierarchical"]
fixtures = ["visible", "hidden_a", "hidden_b", "hidden_c", "hidden_d"]
frozen = {r["fixture"]: r for r in val["k9"] if r["draw"] == 0}
lower, per = 0.0, {}
for f in fixtures:
    se = audit[f][Q]; tv = frozen[f]["truth"]
    vals = [frozen[f][k + "_A"] for k in FAM]
    per[f] = dict(truth=tv, se=se, spread=max(vals) - min(vals),
                  bias=sum(v - tv for v in vals) / 3, worst_valid=max(abs(v - tv) for v in vals) / se)
    lower = max(lower, per[f]["worst_valid"])
wrong = {}
for m in [k for k in val["panel"]["visible"] if k not in ("truth",) and not k.startswith("VARIANT")]:
    wrong[m] = max(abs(val["panel"][f][m] - val["panel"][f]["truth"]) / audit[f][Q] for f in fixtures)
hard = min(wrong, key=wrong.get); upper = wrong[hard]
mult = round(math.sqrt(lower * upper), 1)
print("lower bound (worst legitimate family)      %.2f SE_REF" % lower)
for m, v in sorted(wrong.items(), key=lambda x: x[1]):
    print("  wrong %-26s most-detectable error %.2f SE_REF" % (m, v))
print("upper bound (hardest wrong: %s)  %.2f SE_REF" % (hard, upper))
assert upper > lower, "NO ADMISSIBLE WINDOW"
print("window %.2f < m < %.2f  ->  multiplier %.1f (worst valid at %.2f of tol; hardest wrong caught at %.2fx)"
      % (lower, upper, mult, lower / mult, upper / mult))
print("\n%-9s %9s %9s %9s %9s %9s %9s  %s" % ("fixture", "truth", "SE_REF", "tol", "spread", "bias", "valid/tol", "closest wrong (err/tol)"))
out = {"lower": lower, "upper": upper, "hardest": hard, "multiplier": mult, "fixtures": {}}
for f in fixtures:
    tol = mult * per[f]["se"]
    cw = min(((abs(val["panel"][f][m] - val["panel"][f]["truth"]) / tol, m) for m in wrong))
    per[f].update(tol=tol, closest_wrong=cw[1], closest_wrong_ratio=cw[0])
    print("%-9s %9.5f %9.5f %9.5f %9.5f %+9.5f %9.2f  %s (%.2f)" % (f, per[f]["truth"], per[f]["se"], tol,
          per[f]["spread"], per[f]["bias"], per[f]["worst_valid"] * per[f]["se"] / tol, cw[1], cw[0]))
print("\nDEFINITION VARIANT (not in window) - season-average reduction, err / tol:")
for f in fixtures:
    print("   %-9s %.2f" % (f, abs(val["panel"][f]["VARIANT_season_average"] - val["panel"][f]["truth"]) / per[f]["tol"]))
out["fixtures"] = per
(R / "research/g36/v1_1/tolerance_calibration.json").write_text(json.dumps(out, indent=1))
