#!/usr/bin/env python3
"""Build-time only: reproduce the XP-231 readout history inside the workspace.

- Weekly readouts (2026-08-03 .. 2026-08-31) and the decision readout (2026-09-01): the actual workspace pipeline.
- Readout run log, deployment log, and the Growth PM note quoting the decision readout.
Deleted from the image after the build.
"""
import json
import sys
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(sys.argv[1])
sys.path.insert(0, str(ROOT / "src"))
from xp_analysis.config import load_config  # noqa: E402
from xp_analysis.pipeline import run_readout  # noqa: E402

cfg = load_config(ROOT / "config/xp231.toml")
runs = []
d = date(2026, 8, 3)
while d <= date(2026, 8, 31):
    r = run_readout(cfg, d)
    if d < date(2026, 8, 10):  # runs before the 3.1.0 deployment
        r["code_version"] = "3.0.0"
        r.pop("srm_p_value", None)  # added in 3.1.0
        path = ROOT / f"reports/experiments/XP-231_readout_{d}.json"
        path.write_text(json.dumps(r, indent=2, sort_keys=True) + "\n")
    runs.append((d, r))
    d += timedelta(days=7)
final = run_readout(cfg, date(2026, 9, 1))
runs.append((date(2026, 9, 1), final))

logs = ROOT / "logs"
logs.mkdir(exist_ok=True)
with open(logs / "readout_runs.csv", "w") as fh:
    fh.write("run_id,experiment_id,analysis_date,code_version,status,n_units_control,n_units_treatment,effect,ci_low,ci_high,decision,srm_p_value\n")
    for i, (d, r) in enumerate(runs, 1):
        fh.write(f"xr-{3100 + i},XP-231,{d},{r['code_version']},success,{r['n_units_control']},{r['n_units_treatment']},"
                 f"{r['effect']:.4f},{r['ci_low']:.4f},{r['ci_high']:.4f},{r['decision']},{format(r['srm_p_value'], '.3g') if 'srm_p_value' in r else ''}\n")
(logs / "deployments.csv").write_text("""deployed_at,service,version,summary,ticket
2026-05-28T10:00:00Z,xp-platform,docs,Triggered analysis guidance published,XPP-12
2026-06-15T09:30:00Z,xp_analysis,3.0.0,Exposure-triggered readouts by default,XPP-12
2026-07-06T08:00:00Z,xp-platform,XP-231,XP-231 onboarding checklist started (workspace experiment),GRO-231
2026-07-20T08:00:00Z,xp-platform,XP-240,XP-240 pricing page annual-plan emphasis started (user experiment),MON-240
2026-07-21T09:00:00Z,web-app,2026.07.21,Dashboard performance: data fetch p95 3.8s -> 1.2s,WEB-1880
2026-07-29T14:00:00Z,xp-platform,incident,INC-5521 assignment cache flush,INC-5521
2026-08-03T07:00:00Z,marketing,campaign,Back-to-work paid social campaign (self-serve signups),MKT-311
2026-08-10T11:20:00Z,xp_analysis,3.1.0,SRM check as warning,XPP-19
""")
note = ROOT / "notes/2026-09-01_growth_readout.md"
note.write_text(note.read_text().replace("EFFECT_PP", f"{100 * final['effect']:.1f}")
                .replace("CI_LO", f"{100 * final['ci_low']:.1f}").replace("CI_HI", f"{100 * final['ci_high']:.1f}"))
print(json.dumps([(str(d), round(r["effect"], 4), r["decision"]) for d, r in runs]))
