"""Generate the G34 mutation suite: each writes a complete cli.py with one defect."""
import pathlib

HEAD = '''"""patched analysis"""
from __future__ import annotations
import argparse, json
from pathlib import Path
import numpy as np
from fleet_reliability import history

H = 36.0
TRIG = 0.28
OUT = ("UNPL_FAIL", "PM_OVHL", "ASSET_RET")

def shares(t, kind, horizon=H, causes=OUT):
    o = np.argsort(t); t, kind = t[o], kind[o]
    n = len(t); still = 1.0; acc = {c: 0.0 for c in OUT}; i = 0
    while i < n and t[i] <= horizon:
        q = t[i]; j = i
        while j < n and t[j] == q: j += 1
        ar = n - i; rem = 0
        for c in causes:
            d = int((kind[i:j] == c).sum())
            if d: acc[c] += still * d / ar; rem += d
        still *= 1.0 - rem / ar; i = j
    acc["still"] = still; return acc

def km(t, ev, horizon=H):
    o = np.argsort(t); t, ev = t[o], ev[o]
    n = len(t); S = 1.0; i = 0
    while i < n and t[i] <= horizon:
        q = t[i]; j = i
        while j < n and t[j] == q: j += 1
        d = int(ev[i:j].sum()); S *= 1.0 - d / (n - i); i = j
    return 1.0 - S

def analyse(warehouse: Path, out: Path) -> None:
    df = history.build(warehouse)
    t = df["exit_age"].to_numpy(float); k = df["wo_type"].to_numpy(object)
    n = len(df)
    counts = {c: int((df["wo_type"] == c).sum()) for c in OUT}
    counts["no_work_order"] = int((df["wo_type"] == "").sum())
    at_risk = {str(a): int((df["exit_age"] > a).sum()) for a in (12, 24, 36)}
BODY
    out.mkdir(parents=True, exist_ok=True)
    (out / "analysis_results.json").write_text(json.dumps(payload, indent=2) + "\\n")

def main(argv=None):
    ap = argparse.ArgumentParser(prog="fleet_reliability")
    sub = ap.add_subparsers(dest="command", required=True)
    g = sub.add_parser("analyse"); g.add_argument("--warehouse", default="data/warehouse.sqlite"); g.add_argument("--out", default="out")
    a = ap.parse_args(argv); analyse(Path(a.warehouse), Path(a.out))
'''

PAYLOAD = '''    payload = {{"horizon_months": 36, "installed_base_units": n, "event_counts": counts,
        "units_at_risk": at_risk,
        "aftermarket": {{"unplanned_failure_rate_36m": {q1}, "overhaul_rate_36m": {ov},
            "retirement_rate_36m": {rt}, "still_original_assembly_36m": {sv}}},
        "engineering": {{"assembly_failure_rate_36m": {q2}}},
        "recommendation": "expanded" if ({q1}) > TRIG else "baseline"}}'''

CORRECT = dict(q1='s["UNPL_FAIL"]', ov='s["PM_OVHL"]', rt='s["ASSET_RET"]', sv='s["still"]', q2='km(t, k == "UNPL_FAIL")')

MUT = {}
def m(name, setup, **over):
    d = dict(CORRECT); d.update(over)
    MUT[name] = "    s = shares(t, k)\n" + setup + "\n" + PAYLOAD.format(**d)

m("M00_oracle_equivalent", "")
m("M01_correctQ1_wrongQ2", "", q2='s["UNPL_FAIL"]')
m("M02_wrongQ1_correctQ2", "", q1='km(t, k == "UNPL_FAIL")', sv='1.0 - km(t, k == "UNPL_FAIL")')
m("M03_1km_for_q1", "    f = km(t, k == 'UNPL_FAIL')", q1='f', ov='km(t, k == "PM_OVHL")', rt='km(t, k == "ASSET_RET")', sv='1.0 - f')
# (the slot that held "M04_crude_for_q2" was byte-identical to M01_correctQ1_wrongQ2 - the same
#  substitution under a second name - and was removed rather than replaced with a made-up case.)
m("M05_raw_fraction", "    rf = float(((k == 'UNPL_FAIL') & (t <= H)).sum()) / n", q1='rf', sv='1.0 - rf')
m("M06_cumhaz_as_prob",
  "    ch = 0.0\n"
  "    for a in np.arange(0, H, 1.0):\n"
  "        ar = int((t > a).sum())\n"
  "        if ar == 0: break\n"
  "        ch += int(((t > a) & (t <= a + 1) & (k == 'UNPL_FAIL')).sum()) / ar", q1='ch', sv='1.0 - ch')
m("M07_retirement_censored", "    s = shares(t, np.where(k == 'ASSET_RET', '', k))", rt='0.0')
m("M08_overhaul_censored", "    s = shares(t, np.where(k == 'PM_OVHL', '', k))", ov='0.0')
m("M09_gap_censored",
  "    import sqlite3, pandas as pd\n"
  "    con = sqlite3.connect(str(warehouse)); g = pd.read_sql_query('SELECT unit_id, MIN(gap_start) gs FROM telemetry_status GROUP BY unit_id', con); con.close()\n"
  "    d2 = df.merge(g, on='unit_id', how='left'); d2['gs'] = pd.to_datetime(d2['gs'])\n"
  "    ga = ((d2['gs'] - d2['commissioned_on']).dt.days / 30.4375).to_numpy(float)\n"
  "    hit = np.isfinite(ga) & (ga < t)\n"
  "    t2 = np.where(hit, ga, t); k2 = np.where(hit, '', k)\n"
  "    s = shares(t2, k2)", q2='km(t2, k2 == "UNPL_FAIL")')
m("M10_extract_end_competing", "    s = shares(t, np.where(k == '', 'ASSET_RET', k))")
m("M11_wrong_origin",
  "    t = (df['age_at_cut_off'] - df['exit_age']).to_numpy(float).clip(0.01)\n    s = shares(t, k)", q2='km(t, k == "UNPL_FAIL")')
m("M12_wrong_horizon", "    s = shares(t, k, horizon=24.0)", q2='km(t, k == "UNPL_FAIL", horizon=24.0)')
m("M13_hardcoded_decision", "    s = shares(t, k)\n    _forced = 'expanded'",
  q1='s["UNPL_FAIL"]')
MUT["M13_hardcoded_decision"] = MUT["M13_hardcoded_decision"].replace(
  '"recommendation": "expanded" if (s["UNPL_FAIL"]) > TRIG else "baseline"', '"recommendation": "expanded"')
m("M14_published_55", "", q1='0.552', sv='0.448', q2='0.552')
m("M15_mature_only",
  "    keep = k != ''\n    s = shares(t[keep], k[keep])", q2='km(t[keep], k[keep] == "UNPL_FAIL")')
m("M16_incoherent_decomposition", "", ov='s["PM_OVHL"] * 0.8', rt='s["ASSET_RET"] * 0.8')
m("M17_conservation_violated", "", sv='s["still"] + 0.15')
m("M18_hardcoded_counts", "    counts = {'UNPL_FAIL': 2311, 'PM_OVHL': 3117, 'ASSET_RET': 1146, 'no_work_order': 2426}\n    s = shares(t, k)")
m("M19_all_nonfailure_competing", "    s = shares(t, np.where(k == '', 'ASSET_RET', k))", q2='s["UNPL_FAIL"]')
m("M20_swap_objects", "", q1='km(t, k == "UNPL_FAIL")', q2='s["UNPL_FAIL"]', sv='1.0 - km(t, k == "UNPL_FAIL")')
# M21 is NOT a wrong analysis.  It is the conservative analyst's variation: correct estimators,
# but restricted to units old enough to have been observed for the full 36 months, which sidesteps
# administrative censoring at the cost of discarding most of the fleet.  It is here to measure
# whether a legitimate-but-wasteful route survives the tolerance, not to be rejected.
m("M21_oldest_cohort",
  "    full = df['age_at_cut_off'].to_numpy(float) >= H\n"
  "    t = t[full]; k = k[full]\n"
  "    s = shares(t, k)", q2='km(t, k == "UNPL_FAIL")')

d = pathlib.Path(__file__).parent / "mutations"
d.mkdir(exist_ok=True)
for name, body in MUT.items():
    src = HEAD.replace("BODY", body)
    patch = ('import pathlib\n'
             'p = pathlib.Path("/workspace/fleet_reliability/cli.py")\n'
             'p.write_text(%r)\n' % src)
    (d / (name + ".py")).write_text(patch)
print("wrote", len(MUT), "mutations")
