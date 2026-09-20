"""Local wrong-method / valid-route panel on the IMPLEMENTED G35 extract.

Measures each analysis's error against latent truth, per fixture, so the tolerance multiplier can be
chosen from the measured gap between valid routes and wrong analyses rather than inherited.
Research/dev only: no model, no container.

    python tools/g35/analysis_panel.py
"""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2] / "candidates" / "g35-dispatch-priority-gate"
sys.path.insert(0, str(ROOT / "tests"))
sys.path.insert(0, str(ROOT / "environment" / "build"))
sys.path.insert(0, str(ROOT / "solution"))
import world, scenarios                                            # noqa: E402
from dispatch_experiment import estimate, load                     # noqa: E402

Q = scenarios.QUANT


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


def analyses(blocks):
    t50, c50 = _half(blocks)
    direct, spill = t50 - c50, c50 - _arm(blocks, 0.0)
    policy = _arm(blocks, 1.0) - _arm(blocks, 0.0)
    pooled = _pooled(blocks)
    t25, c25 = _half(blocks, 0.25)

    sz = sorted(sum(r["orders_requested"] for r in b["rows"]) for b in blocks)
    cut = sz[len(sz) // 4]
    big = [b for b in blocks if sum(r["orders_requested"] for r in b["rows"]) >= cut]

    def _uw(s):
        v = [sum(r["orders_delivered"] for r in b["rows"])
             / max(sum(r["orders_requested"] for r in b["rows"]), 1)
             for b in blocks if abs(b["assigned_saturation"] - s) < 1e-9]
        return sum(v) / len(v) if v else 0.0

    num = den = 0.0
    for b in blocks:
        tn = td = cn = cd = 0.0
        for r in b["rows"]:
            if r["assigned_priority"]:
                tn += r["orders_delivered"]; td += r["orders_requested"]
            else:
                cn += r["orders_delivered"]; cd += r["orders_requested"]
        if td > 0 and cd > 0:
            w = td + cd
            num += (tn / td - cn / cd) * w; den += w
    bfe = num / den if den else 0.0

    out = {
        "V00_oracle": dict(direct_effect_50=direct, spillover_50=spill,
                           policy_effect_full=policy),
        "V02_largest_blocks": dict(direct_effect_50=direct, spillover_50=spill,
                                   policy_effect_full=_arm(big, 1.0) - _arm(big, 0.0)),
        "W01_naive_ab": dict(direct_effect_50=direct, spillover_50=spill,
                             policy_effect_full=pooled),
        "W03_direct_as_policy": dict(direct_effect_50=direct, spillover_50=spill,
                                     policy_effect_full=direct),
        "W04_total_at_50": dict(direct_effect_50=direct, spillover_50=spill,
                                policy_effect_full=_arm(blocks, 0.5) - _arm(blocks, 0.0)),
        "W05_direct_plus_spill": dict(direct_effect_50=direct, spillover_50=spill,
                                      policy_effect_full=direct + spill),
        "W06_spillover_zero": dict(direct_effect_50=direct, spillover_50=0.0,
                                   policy_effect_full=policy),
        "W08_block_fe": dict(direct_effect_50=direct, spillover_50=spill,
                             policy_effect_full=bfe),
        "W09_unweighted": dict(direct_effect_50=direct, spillover_50=spill,
                               policy_effect_full=_uw(1.0) - _uw(0.0)),
        "W16_direct_at_25": dict(direct_effect_50=direct, spillover_50=spill,
                                 policy_effect_full=t25 - c25),
        "W17_arm_75_as_full": dict(direct_effect_50=direct, spillover_50=spill,
                                   policy_effect_full=_arm(blocks, 0.75) - _arm(blocks, 0.0)),
        "W20_extrapolate_25": dict(direct_effect_50=direct, spillover_50=spill,
                                   policy_effect_full=(_arm(blocks, 0.25) - _arm(blocks, 0.0)) / 0.25),
    }
    return out


def main():
    rows = {}
    truths = {}
    for name in scenarios.ALL_NAMES:
        w = world.build(scenarios.by_name(name))
        truths[name] = world.truth(w)
        d = tempfile.mkdtemp()
        db = world.write_sqlite(w, d)
        rows[name] = analyses(load.blocks(db))

    print("Error against latent truth, fulfilment-rate points.  |err| / SE_REF in brackets.")
    have_se = bool(scenarios.SE_REF)
    for q in Q:
        print("\n--- %s ---" % q)
        print("%-24s %s" % ("analysis", "".join("%18s" % n for n in scenarios.ALL_NAMES)))
        for a in rows[scenarios.ALL_NAMES[0]]:
            line = ""
            for n in scenarios.ALL_NAMES:
                err = rows[n][a][q] - truths[n][q]
                if have_se:
                    line += "%12.4f(%4.1f)" % (err, abs(err) / scenarios.SE_REF[n][q])
                else:
                    line += "%18.4f" % err
            print("%-24s %s" % (a, line))

    print("\n--- decision implied by policy_effect_full ---")
    print("%-24s %s" % ("analysis", "".join("%14s" % n for n in scenarios.ALL_NAMES)))
    for a in rows[scenarios.ALL_NAMES[0]]:
        line = ""
        for n in scenarios.ALL_NAMES:
            d = "launch" if rows[n][a]["policy_effect_full"] >= 0.015 else "hold"
            line += "%14s" % (d + ("" if d == truths[n]["decision"] else "*"))
        print("%-24s %s" % (a, line))
    print("\n truth: %s" % "  ".join("%s=%s" % (n, truths[n]["decision"]) for n in scenarios.ALL_NAMES))


if __name__ == "__main__":
    main()
