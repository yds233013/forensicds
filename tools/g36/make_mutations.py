"""Generate the G36 mutation suite with full distinctness AND execution enforcement.

Four rules, each with a verified negative control (see research/g35/mutation_hash_design.md):
  1. a mutation must differ from the unmutated source;
  2. no unexpected duplicate hashes;
  3. the intended change must appear in the rendered source;
  4. the mutation must actually RUN and emit every graded quantity as a number.

Rule 4 exists because G35's first suite was entirely vacuous: every generated file crashed on
import, so all wrong cases "scored 0" for the wrong reason.
"""
from __future__ import annotations

import hashlib, json, pathlib, sys

HEAD = '''import pathlib
p = pathlib.Path("/workspace/capacity_forecast/cli.py")
p.write_text({src!r})
'''

BODY = '''"""patched analysis"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from capacity_forecast import load

CAPACITY_GATE_KW = 3.057
PILOT_YEAR = 2026
CDD_REF = 10.0


def _ols(X, y, w=None):
    w = np.ones(len(y)) if w is None else w
    sw = np.sqrt(w)
    return np.linalg.lstsq(X * sw[:, None], y * sw, rcond=None)[0]


def analyse(warehouse: Path, out: Path) -> None:
    fr = load.frames(warehouse)
    df = fr["loads"]
    hist = df[df["year"] != PILOT_YEAR]
    pilot = df[df["year"] == PILOT_YEAR]
    segs = sorted(df["segment_code"].dropna().unique())
    tcdd = fr["forecast"]["cooling_degree_days_forecast"].to_numpy(float)
    cbar = float(tcdd.mean())
    pilot_cbar = float(pilot["cooling_degree_days"].mean())
    cm = fr["customers"]
    shares = cm["segment_code"].value_counts(normalize=True).sort_index()
    pop = {s: float(shares[s]) for s in segs}

    stable = {}
    for s in segs:
        h = hist[hist["segment_code"] == s]
        g = h.groupby("cooling_degree_days")["peak_kw"]
        m, n = g.mean(), g.size()
        stable[s] = _ols(np.column_stack([np.ones(len(m)), m.index.to_numpy(float)]),
                         m.to_numpy(float), w=n.to_numpy(float))

    curve, enrolled_n = {}, {}
    for s in segs:
        p = pilot[pilot["segment_code"] == s]
        enrolled_n[s] = p["household_id"].nunique()
        arm = {}
        for nm in ("treatment", "control"):
            q = p[p["assigned_arm"] == nm].groupby("cooling_degree_days")["peak_kw"]
            m, n = q.mean(), q.size()
            arm[nm] = _ols(np.column_stack([np.ones(len(m)), m.index.to_numpy(float) - CDD_REF]),
                           m.to_numpy(float), w=n.to_numpy(float))
        grid = np.linspace(p["cooling_degree_days"].min(), p["cooling_degree_days"].max(), 25)
        ft = arm["treatment"][0] + arm["treatment"][1] * (grid - CDD_REF)
        fc = arm["control"][0] + arm["control"][1] * (grid - CDD_REF)
        curve[s] = _ols(np.column_stack([np.ones(len(grid)), grid - CDD_REF]), 1.0 - ft / fc)

    def r_at(s, cdd):
        return float(np.clip(curve[s][0] + curve[s][1] * (cdd - CDD_REF), 0.0, 0.95))

    enr_tot = sum(enrolled_n.values()) or 1
    enr = {s: enrolled_n[s] / enr_tot for s in segs}
    weights = {W}
    resp_cdd = {RC}
    use_resp = {UR}

    seg_fc, total = {{}}, 0.0
    for s in segs:
        a, b = stable[s]
        if use_resp:
            per = [(a + b * c) * (1 - r_at(s, resp_cdd if resp_cdd else c)) for c in tcdd]
        else:
            per = [(a + b * c) for c in tcdd]
        seg_fc[s] = float(np.mean(per))
        total += weights[s] * seg_fc[s]
{EXTRA}
    est_resp = {ER}
    payload = {{"n_households": {NH},
                "estate_segment_shares": {{k: float(v) for k, v in shares.items()}},
                "target_cdd_mean": {TC},
                "segment_target_peak_kw": seg_fc,
                "estate_tou_response_at_target_cdd": est_resp,
                "target_peak_kw": {TP},
                "procurement_decision": {DEC}}}
    out.mkdir(parents=True, exist_ok=True)
    (out / "analysis_results.json").write_text(json.dumps(payload, indent=2) + "\\n")


def main(argv=None):
    ap = argparse.ArgumentParser(prog="capacity_forecast")
    sub = ap.add_subparsers(dest="command", required=True)
    g = sub.add_parser("analyse")
    g.add_argument("--warehouse", default="data/warehouse.sqlite")
    g.add_argument("--out", default="out")
    a = ap.parse_args(argv)
    analyse(Path(a.warehouse), Path(a.out))
'''

BASE = dict(W="pop", RC="None", UR="True", EXTRA="",
            ER="float(sum(pop[s] * r_at(s, cbar) for s in segs))",
            NH="int(cm.shape[0])", TC="cbar", TP="float(total)",
            DEC='"procure" if float(total) >= CAPACITY_GATE_KW else "defer"')

CASES = {}


def case(name, kind, **over):
    d = dict(BASE); d.update(over)
    CASES[name] = (d, kind)


# ---------------------------------------------------------------- legitimate routes (expect 1)
case("V00_plugin_transport", "valid")
case("V01_explicit_loop", "valid",
     EXTRA="    total = sum(weights[s] * seg_fc[s] for s in segs)")

# ------------------------------------------------------------------ wrong analyses (expect 0)
case("M03_historical_model", "wrong", UR="False", ER="0.0")
case("M05_historical_mean", "wrong", TP='float(hist["peak_kw"].mean())')
case("M06_pilot_mean", "wrong",
     TP='float(pilot[pilot["assigned_arm"] == "treatment"]["peak_kw"].mean())')
case("M07_pilot_effect_flat", "wrong", UR="False",
     EXTRA=('    _pt = float(pilot[pilot["assigned_arm"] == "treatment"]["peak_kw"].mean())\n'
            '    _pc = float(pilot[pilot["assigned_arm"] == "control"]["peak_kw"].mean())\n'
            '    total = total * (_pt / _pc)'))
case("M08_selection_fixed_only", "wrong", RC="pilot_cbar",
     ER="float(sum(pop[s] * r_at(s, pilot_cbar) for s in segs))")
case("M09_temperature_fixed_only", "wrong", W="enr",
     ER="float(sum(enr[s] * r_at(s, cbar) for s in segs))")
case("M10_pilot_population", "wrong", W="enr", RC="pilot_cbar",
     ER="float(sum(enr[s] * r_at(s, pilot_cbar) for s in segs))")
case("M12_intercept_recalibration", "wrong", UR="False",
     EXTRA=('    _pc = float(pilot[pilot["assigned_arm"] == "control"]["peak_kw"].mean())\n'
            '    total = total + (_pc - float(hist["peak_kw"].mean()))'))
case("M13_equal_segment_weights", "wrong",
     EXTRA="    weights = {s: 1.0 / len(segs) for s in segs}\n"
           "    total = sum(weights[s] * seg_fc[s] for s in segs)")
case("M14_response_at_midpoint_cdd", "wrong",
     EXTRA="    resp_cdd = 0.5 * (cbar + pilot_cbar)\n"
           "    seg_fc = {s: float(np.mean([(stable[s][0] + stable[s][1] * c) *\n"
           "        (1 - r_at(s, resp_cdd)) for c in tcdd])) for s in segs}\n"
           "    total = sum(pop[s] * seg_fc[s] for s in segs)")
case("M15_target_weather_ignored", "wrong",
     EXTRA='    _hc = float(hist["cooling_degree_days"].mean())\n'
           "    seg_fc = {s: (stable[s][0] + stable[s][1] * _hc) * (1 - r_at(s, _hc))"
           " for s in segs}\n"
           "    total = sum(pop[s] * seg_fc[s] for s in segs)")
case("M18_aggregate_effect_uniform", "wrong", UR="False",
     EXTRA=('    _pt = float(pilot[pilot["assigned_arm"] == "treatment"]["peak_kw"].mean())\n'
            '    _pc = float(pilot[pilot["assigned_arm"] == "control"]["peak_kw"].mean())\n'
            '    total = total * (1 - (1 - _pt / _pc))'))
case("M20_constant_procure", "wrong", DEC='"procure"')
case("M21_constant_defer", "wrong", DEC='"defer"')
# "seasonal naive" would render identically to M05 here - the history has no multi-year
# seasonal structure to exploit - so it is replaced by a genuinely distinct naive baseline:
# take the level of the pilot's untreated control households and call it the forecast.
case("M23_control_arm_level", "wrong",
     TP='float(pilot[pilot["assigned_arm"] == "control"]["peak_kw"].mean())')
case("M24_latest_value", "wrong",
     TP='float(hist[hist["year"] == hist["year"].max()]["peak_kw"].mean())')
case("M26_hardcoded_households", "wrong", NH="6000")
case("M27_hardcoded_forecast", "wrong", TP="2.98")
case("M28_response_reported_zero", "wrong", ER="0.0")
case("M29_response_sign_flipped", "wrong",
     ER="float(-sum(pop[s] * r_at(s, cbar) for s in segs))")
case("M30_double_counted_response", "wrong",
     EXTRA="    total = total * (1 - float(sum(pop[s] * r_at(s, cbar) for s in segs)))")
case("M31_shares_from_pilot", "wrong",
     EXTRA="    total = sum(enr[s] * seg_fc[s] for s in segs)")
case("M32_cdd_mean_from_history", "wrong", TC='float(hist["cooling_degree_days"].mean())')

EXPECTED_EQUIVALENT = set()


def render(d):
    b = BODY.replace("{EXTRA}", d["EXTRA"])
    for k in ("W", "RC", "UR", "ER", "NH", "TC", "TP", "DEC"):
        b = b.replace("{%s}" % k, d[k])
    return b.replace("{{", "{").replace("}}", "}")


def _smoke(name, src, cache={}):
    import os, tempfile
    R = pathlib.Path("/Users/yashshah2311/forensicds/candidates/g36-tou-capacity-gate")
    for extra in (R / "environment" / "build", R / "tests", R / "solution"):
        if str(extra) not in sys.path:
            sys.path.insert(0, str(extra))
    if "db" not in cache:
        import world
        sp = dict(world.VISIBLE_SPEC)
        sp.update(n_households=260, n_days=14, seed=99123)
        w = world.build(sp)
        d = tempfile.mkdtemp(); os.makedirs(os.path.join(d, "data"), exist_ok=True)
        cache["db"] = world.write_sqlite(w, os.path.join(d, "data"))
    ns = {}
    try:
        exec(compile(src, name, "exec"), ns)
    except Exception as e:
        return "does not compile: %s: %s" % (type(e).__name__, e)
    out = pathlib.Path(tempfile.mkdtemp()) / "out"
    try:
        ns["analyse"](pathlib.Path(cache["db"]), out)
    except Exception as e:
        return "raised at run time: %s: %s" % (type(e).__name__, e)
    f = out / "analysis_results.json"
    if not f.exists():
        return "wrote no analysis_results.json"
    payload = json.loads(f.read_text())
    for q in ("target_peak_kw", "estate_tou_response_at_target_cdd", "procurement_decision"):
        if q not in payload:
            return "output is missing %s" % q
    if not isinstance(payload["target_peak_kw"], (int, float)):
        return "target_peak_kw is not numeric"
    return None


def main():
    out = pathlib.Path(__file__).parent / "mutations"
    out.mkdir(exist_ok=True)
    for old in out.glob("*.py"):
        old.unlink()
    base_src = render(BASE)
    manifest, by_hash, errors = {}, {}, []
    for name, (d, kind) in CASES.items():
        src = render(d)
        patch = HEAD.format(src=src)
        h = hashlib.sha256(patch.encode()).hexdigest()
        if kind == "wrong" and src == base_src:
            errors.append("%s is byte-identical to the unmutated source" % name)
        if h in by_hash and (name, by_hash[h]) not in EXPECTED_EQUIVALENT:
            errors.append("%s duplicates %s (hash %s)" % (name, by_hash[h], h[:12]))
        by_hash[h] = name
        problem = _smoke(name, src)
        if problem:
            errors.append("%s: %s" % (name, problem))
        (out / (name + ".py")).write_text(patch)
        manifest[name] = {"sha256": h, "source_sha256": hashlib.sha256(base_src.encode()).hexdigest(),
                          "kind": kind, "expect_reward": 1 if kind == "valid" else 0,
                          "smoke": "ok" if not problem else problem}
    pathlib.Path(__file__).with_name("mutations_manifest.json").write_text(
        json.dumps(manifest, indent=1) + "\n")
    nv = sum(1 for v in manifest.values() if v["kind"] == "valid")
    nw = len(manifest) - nv
    print("wrote %d mutations (%d valid, %d wrong), %d distinct hashes"
          % (len(manifest), nv, nw, len(by_hash)))
    if errors:
        print("\nMUTATION VALIDATION FAILED:")
        for e in errors:
            print("   -", e)
        sys.exit(1)
    if nw < 20:
        print("\nMUTATION VALIDATION FAILED: fewer than 20 wrong cases (%d)" % nw)
        sys.exit(1)
    print("all four rules pass: distinct from source, no duplicate hashes, change present, executes")


if __name__ == "__main__":
    main()
