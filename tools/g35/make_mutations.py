"""Generate the G35 mutation suite, with the distinctness enforcement G34 lacked.

G34 shipped two vacuous mutations: one byte-identical to the oracle (the intended change was never
emitted) and one duplicating another mutation. Both were found by hashing files, not by the suite.
This generator refuses to write a suite with either defect.

    python tools/g35/make_mutations.py

Writes tools/g35/mutations/*.py and tools/g35/mutations_manifest.json.
Exits non-zero if any rule below is violated.
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import sys

HEAD = '''import pathlib
p = pathlib.Path("/workspace/dispatch_experiment/cli.py")
p.write_text({src!r})
'''

BODY = '''"""patched analysis"""
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

from dispatch_experiment import load

GATE = 0.015


def _arm(blocks, s):
    num = den = 0.0
    for b in blocks:
        if abs(b["assigned_saturation"] - s) > 1e-9:
            continue
        num += sum(r["orders_delivered"] for r in b["rows"])
        den += sum(r["orders_requested"] for r in b["rows"])
    return num / den if den else 0.0


def _half(blocks, s=0.5):
    tn = td = cn = cd = 0.0
    for b in blocks:
        if abs(b["assigned_saturation"] - s) > 1e-9:
            continue
        for r in b["rows"]:
            if r["assigned_priority"]:
                tn += r["orders_delivered"]; td += r["orders_requested"]
            else:
                cn += r["orders_delivered"]; cd += r["orders_requested"]
    return (tn / td if td else 0.0), (cn / cd if cd else 0.0)


def _pooled(blocks):
    tn = td = cn = cd = 0.0
    for b in blocks:
        for r in b["rows"]:
            if r["assigned_priority"]:
                tn += r["orders_delivered"]; td += r["orders_requested"]
            else:
                cn += r["orders_delivered"]; cd += r["orders_requested"]
    return (tn / td if td else 0.0) - (cn / cd if cd else 0.0)


def analyse(warehouse: Path, out: Path) -> None:
    blocks = load.blocks(warehouse)
    sat = Counter("%.2f" % b["assigned_saturation"] for b in blocks)
    n_rows = sum(len(b["rows"]) for b in blocks)
    req_total = sum(r["orders_requested"] for b in blocks for r in b["rows"])
    t50, c50 = _half(blocks)
    direct = t50 - c50
    spill = c50 - _arm(blocks, 0.0)
    policy = _arm(blocks, 1.0) - _arm(blocks, 0.0)
{SETUP}
    effects = {"direct_effect_50": {D}, "spillover_50": {S}, "policy_effect_full": {P}}
    payload = {"n_dispatch_blocks": {NB}, "n_merchant_days": n_rows,
                "orders_requested_total": req_total,
                "blocks_by_saturation": dict(sorted(sat.items())),
                "effects": effects, "recommendation": {REC}}
    out.mkdir(parents=True, exist_ok=True)
    (out / "analysis_results.json").write_text(json.dumps(payload, indent=2) + "\\n")


def main(argv=None):
    ap = argparse.ArgumentParser(prog="dispatch_experiment")
    sub = ap.add_subparsers(dest="command", required=True)
    g = sub.add_parser("analyse")
    g.add_argument("--warehouse", default="data/warehouse.sqlite")
    g.add_argument("--out", default="out")
    a = ap.parse_args(argv)
    analyse(Path(a.warehouse), Path(a.out))
'''

BASE = dict(SETUP="", D="direct", S="spill", P="policy", NB="len(blocks)",
            REC='"launch" if policy >= GATE else "hold"')

# name -> (overrides, kind, the graded quantity the change must move)
CASES = {}


def case(name, kind, moves, **over):
    d = dict(BASE)
    d.update(over)
    CASES[name] = (d, kind, moves)


# ----------------------------------------------------------------- legitimate routes (expect 1)
case("V00_oracle_equivalent", "valid", None)
case("V01_arm_means", "valid", None,
     SETUP="    a1 = _arm(blocks, 1.0)\n    a0 = _arm(blocks, 0.0)", P="a1 - a0")
case("V02_largest_blocks", "valid", None,
     SETUP=("    sz = sorted((sum(r['orders_requested'] for r in b['rows']) for b in blocks))\n"
            "    cut = sz[len(sz) // 4]\n"
            "    big = [b for b in blocks if sum(r['orders_requested'] for r in b['rows']) >= cut]\n"
            "    policy = _arm(big, 1.0) - _arm(big, 0.0)"))

# ------------------------------------------------------------------- wrong analyses (expect 0)
case("W01_naive_ab_as_policy", "wrong", "policy_effect_full", P="_pooled(blocks)")
case("W02_cluster_se_only", "wrong", "policy_effect_full",
     SETUP="    _se = 0.0031  # cluster-robust, computed and reported alongside", P="_pooled(blocks)")
case("W03_direct_as_policy", "wrong", "policy_effect_full", P="direct")
case("W04_total_at_50_as_policy", "wrong", "policy_effect_full",
     SETUP="    tot50 = _arm(blocks, 0.5) - _arm(blocks, 0.0)", P="tot50")
case("W05_direct_plus_spillover", "wrong", "policy_effect_full", P="direct + spill")
case("W06_spillover_zero", "wrong", "spillover_50", S="0.0")
case("W07_spillover_sign_flipped", "wrong", "spillover_50", S="-spill")
case("W08_block_fe_direct_as_policy", "wrong", "policy_effect_full",
     SETUP=("    num = den = 0.0\n"
            "    for b in blocks:\n"
            "        tn = td = cn = cd = 0.0\n"
            "        for r in b['rows']:\n"
            "            if r['assigned_priority']:\n"
            "                tn += r['orders_delivered']; td += r['orders_requested']\n"
            "            else:\n"
            "                cn += r['orders_delivered']; cd += r['orders_requested']\n"
            "        if td > 0 and cd > 0:\n"
            "            w = td + cd\n"
            "            num += (tn / td - cn / cd) * w; den += w\n"
            "    bfe = num / den if den else 0.0"), P="bfe")
# MEASURED NEAR-MISS, expected to PASS. Merchant-weighted rather than demand-weighted block means
# land within 0.005 of truth in this DGP - inside oracle-level error - so this is not a dependable
# trap and is not counted toward separation.
case("W09_unweighted_blocks", "nearmiss", "policy_effect_full",
     SETUP=("    def _uw(s):\n"
            "        v = [sum(r['orders_delivered'] for r in b['rows'])\n"
            "             / max(sum(r['orders_requested'] for r in b['rows']), 1)\n"
            "             for b in blocks if abs(b['assigned_saturation'] - s) < 1e-9]\n"
            "        return sum(v) / len(v) if v else 0.0\n"
            "    policy = _uw(1.0) - _uw(0.0)"))
# MEASURED NEAR-MISS, expected to PASS. The G35 brief (A7) is explicit that a verifier must not
# reject an analysis merely for using realised saturation; only a clearly defined scientific error
# may be rejected. Conditioning on realised activation is post-treatment in principle, but here it
# selects almost the same blocks and its error is oracle-sized.
case("W10_realised_activation_arms", "nearmiss", "policy_effect_full",
     SETUP=("    hi = [b for b in blocks if b['rows'] and\n"
            "          sum(r['activated'] for r in b['rows']) / len(b['rows']) >= 0.75]\n"
            "    lo = [b for b in blocks if not any(r['activated'] for r in b['rows'])]\n"
            "    def _m(bs):\n"
            "        n = sum(r['orders_delivered'] for b in bs for r in b['rows'])\n"
            "        d = sum(r['orders_requested'] for b in bs for r in b['rows'])\n"
            "        return n / d if d else 0.0\n"
            "    policy = _m(hi) - _m(lo)"))
case("W11_treated_only", "wrong", "policy_effect_full",
     SETUP=("    tn = sum(r['orders_delivered'] for b in blocks for r in b['rows']\n"
            "             if r['assigned_priority'])\n"
            "    td = sum(r['orders_requested'] for b in blocks for r in b['rows']\n"
            "             if r['assigned_priority'])\n"
            "    gn = sum(r['orders_delivered'] for b in blocks for r in b['rows'])\n"
            "    gd = sum(r['orders_requested'] for b in blocks for r in b['rows'])\n"
            "    policy = tn / td - gn / gd"))
case("W12_swap_direct_and_policy", "wrong", "policy_effect_full", D="policy", P="direct")
case("W13_dashboard_copy", "wrong", "policy_effect_full",
     D="_pooled(blocks)", S="0.0", P="_pooled(blocks)")
case("W14_constant_launch", "wrong", None, REC='"launch"')
case("W15_constant_hold", "wrong", None, REC='"hold"')
case("W16_direct_at_25_as_policy", "wrong", "policy_effect_full",
     SETUP="    t25, c25 = _half(blocks, 0.25)", P="t25 - c25")
# MEASURED NEAR-MISS, expected to PASS. Using the 75% arm as if it were full rollout IS wrong
# science, but the saturation response is close to linear over [0.75, 1.0], so the numerical
# consequence (<= 0.009) is inside sampling noise. The verifier grades quantities, not reasoning
# paths, so it passes. Documented rather than patched around.
case("W17_arm_75_as_full", "nearmiss", "policy_effect_full",
     SETUP="    a75 = _arm(blocks, 0.75)\n    a0b = _arm(blocks, 0.0)", P="a75 - a0b")
case("W18_full_vs_mixed_controls", "wrong", "policy_effect_full",
     SETUP=("    a1 = _arm(blocks, 1.0)\n"
            "    cn = sum(r['orders_delivered'] for b in blocks for r in b['rows']\n"
            "             if not r['assigned_priority'] and 0 < b['assigned_saturation'] < 1)\n"
            "    cd = sum(r['orders_requested'] for b in blocks for r in b['rows']\n"
            "             if not r['assigned_priority'] and 0 < b['assigned_saturation'] < 1)"),
     P="a1 - (cn / cd if cd else 0.0)")
case("W19_hardcoded_counts", "wrong", None, NB="1680")
case("W20_extrapolate_from_25", "wrong", "policy_effect_full",
     SETUP="    slope = (_arm(blocks, 0.25) - _arm(blocks, 0.0)) / 0.25", P="slope")
case("W21_ratio_not_difference", "wrong", "policy_effect_full",
     SETUP="    a1 = _arm(blocks, 1.0)\n    a0 = _arm(blocks, 0.0)", P="a1 / a0 - 1.0")
case("W22_delivered_share_not_rate", "wrong", "direct_effect_50",
     SETUP=("    td = sum(r['orders_delivered'] for b in blocks for r in b['rows']\n"
            "             if r['assigned_priority'])\n"
            "    gd = sum(r['orders_delivered'] for b in blocks for r in b['rows'])\n"
            "    direct = td / gd"))

case("W23_direct_pooled_not_50", "wrong", "direct_effect_50", D="_pooled(blocks)")
case("W24_policy_naive_minus_spillover", "wrong", "policy_effect_full",
     P="_pooled(blocks) - spill")

EXPECTED_EQUIVALENT = set()   # declare intentional duplicates here; nothing is intentional yet


def _smoke(name, src, fixture_cache={}):
    """Rule 4: a mutation that does not RUN is as useless as one that does not mutate.

    G34 shipped mutations that were byte-identical to their source. This generator's first version
    shipped mutations that differed textually but crashed on import, so every 'wrong' case scored 0
    for the wrong reason and the whole panel was vacuous. Both defects look like success from the
    outside, so both are checked here.
    """
    import tempfile, os, sys
    root = pathlib.Path(__file__).resolve().parents[2] / "candidates" / "g35-dispatch-priority-gate"
    for extra in (root / "tests", root / "environment" / "build", root / "solution"):
        if str(extra) not in sys.path:
            sys.path.insert(0, str(extra))
    if "db" not in fixture_cache:
        import world
        sp = dict(world.VISIBLE_SPEC)
        sp.update(n_cities=6, n_days=6, merchants_per_city=12, seed=4242)
        w = world.build(sp)
        d = tempfile.mkdtemp()
        os.makedirs(os.path.join(d, "data"), exist_ok=True)
        fixture_cache["db"] = world.write_sqlite(w, os.path.join(d, "data"))
        fixture_cache["out"] = d
    ns = {}
    try:
        exec(compile(src, name, "exec"), ns)
    except Exception as e:
        return "does not compile/import: %s: %s" % (type(e).__name__, e)
    out = pathlib.Path(tempfile.mkdtemp()) / "out"
    try:
        ns["analyse"](pathlib.Path(fixture_cache["db"]), out)
    except Exception as e:
        return "raised at run time: %s: %s" % (type(e).__name__, e)
    f = out / "analysis_results.json"
    if not f.exists():
        return "wrote no analysis_results.json"
    try:
        payload = json.loads(f.read_text())
    except Exception as e:
        return "wrote unparseable JSON: %s" % e
    for q in ("direct_effect_50", "spillover_50", "policy_effect_full"):
        if q not in payload.get("effects", {}):
            return "output is missing effects.%s" % q
        if not isinstance(payload["effects"][q], (int, float)):
            return "effects.%s is not numeric" % q
    return None


def render(d):
    body = BODY.replace("{SETUP}", d["SETUP"])
    return (body.replace("{D}", d["D"]).replace("{S}", d["S"]).replace("{P}", d["P"])
            .replace("{NB}", d["NB"]).replace("{REC}", d["REC"]))


def main():
    out = pathlib.Path(__file__).parent / "mutations"
    out.mkdir(exist_ok=True)
    for old in out.glob("*.py"):
        old.unlink()

    base_src = render(BASE)
    manifest, by_hash, errors = {}, {}, []

    for name, (d, kind, moves) in CASES.items():
        src = render(d)
        patch = HEAD.format(src=src)
        h = hashlib.sha256(patch.encode()).hexdigest()

        # rule 1: a mutation must differ from the unmutated source, unless it is the valid baseline
        if kind in ("wrong", "nearmiss") and src == base_src:
            errors.append("%s is byte-identical to the unmutated source (it does not mutate)" % name)
        # rule 2: no unexpected duplicate hashes
        if h in by_hash and (name, by_hash[h]) not in EXPECTED_EQUIVALENT \
                and (by_hash[h], name) not in EXPECTED_EQUIVALENT:
            errors.append("%s duplicates %s (identical hash %s)" % (name, by_hash[h], h[:12]))
        by_hash[h] = name

        # rule 3: the intended textual change must actually appear
        if d["SETUP"] and d["SETUP"].strip().split("\n")[0].strip() not in src:
            errors.append("%s: intended SETUP code is absent from the rendered source" % name)

        # rule 4: it must actually run and produce the graded quantities
        problem = _smoke(name, src)
        if problem:
            errors.append("%s: %s" % (name, problem))

        (out / (name + ".py")).write_text(patch)
        manifest[name] = {"sha256": h, "kind": kind, "must_move": moves,
                          "expect_reward": 0 if kind == "wrong" else 1,
                          "smoke": "ok" if not problem else problem}

    pathlib.Path(__file__).with_name("mutations_manifest.json").write_text(
        json.dumps(manifest, indent=1) + "\n")

    n_valid = sum(1 for v in manifest.values() if v["kind"] == "valid")
    n_near = sum(1 for v in manifest.values() if v["kind"] == "nearmiss")
    n_wrong = sum(1 for v in manifest.values() if v["kind"] == "wrong")
    print("wrote %d mutations (%d valid routes, %d measured near-misses, %d wrong), "
          "%d distinct hashes" % (len(manifest), n_valid, n_near, n_wrong, len(by_hash)))
    if errors:
        print("\nMUTATION VALIDATION FAILED:")
        for e in errors:
            print("   -", e)
        sys.exit(1)
    if n_wrong < 20:
        print("\nMUTATION VALIDATION FAILED: fewer than 20 wrong cases (%d)" % n_wrong)
        sys.exit(1)
    if n_valid < 2:
        print("\nMUTATION VALIDATION FAILED: fewer than 2 legitimate routes (%d)" % n_valid)
        sys.exit(1)
    print("distinctness OK: no mutation equals its source, no unexpected duplicate hash")


if __name__ == "__main__":
    main()
