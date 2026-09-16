#!/usr/bin/env python3
"""Reproduce the operating history of the G24 workspace after the extract is generated (build stage only).

- runs the deployed offline gate and leaves its outputs in out/ope;
- writes the two gate reports (v7, then v7_pd) from the gate's own numbers;
- writes the AB-1182 readout from the logs (responses per arm, clicks per response, member counts);
- writes the June IPS notebook, whose numbers come from the logged propensity field.
"""
from __future__ import annotations

import json
import math
import sqlite3
import subprocess
import sys
from pathlib import Path


def main(root: Path) -> None:
    sys.path.insert(0, str(root.resolve()))
    for sub in ("reports/offline_gate", "reports/ab", "notebooks", "out"):
        (root / sub).mkdir(parents=True, exist_ok=True)
    subprocess.run([sys.executable, "-m", "recs_eval", "ope", "--logs", "data/logs.sqlite", "--out", "out/ope"],
                   cwd=root, check=True)
    import csv as _csv
    gate = {r["policy"]: r for r in _csv.DictReader(open(root / "out/ope/policy_values.csv"))}
    v = lambda p: float(gate[p]["value"])
    lift_pct = lambda p: 100 * (v(p) / v("v6") - 1)

    (root / "reports/offline_gate/2026-08-28_v7_gate.md").write_text(f"""# Offline gate: v7 vs v6 (28 August 2026)

Ranking asked for a gate run on v7 before the launch review.

| Ranker | Gate score (CTR@5) | vs v6 |
|---|---:|---:|
| v6 (production) | {v('v6'):.4f} | — |
| v7 | {v('v7'):.4f} | {lift_pct('v7'):+.1f}% |

Method: `recs_eval` 1.4 replays each ranker on logged responses and scores the slots where the ranker agrees with
what was shown (`RELEASES.md`). Run on the production stream, where candidate lists are logged.

**Read-out:** v7 clears the launch bar on the gate. Ranking has asked Experimentation for an online test.
""")

    (root / "reports/offline_gate/2026-08-30_v7pd_gate.md").write_text(f"""# Offline gate: v7_pd (30 August 2026)

Second candidate, trained on the exploration stream.

| Ranker | Gate score (CTR@5) | vs v6 |
|---|---:|---:|
| v6 (production) | {v('v6'):.4f} | — |
| v7 | {v('v7'):.4f} | {lift_pct('v7'):+.1f}% |
| v7_pd | {v('v7_pd'):.4f} | {lift_pct('v7_pd'):+.1f}% |

Same gate as the v7 run. No online test has been scheduled for v7_pd.
""")

    con = sqlite3.connect(root / "data/logs.sqlite")
    rows = con.execute("""
        SELECT s.ab_arm, COUNT(*) AS serves, COUNT(DISTINCT s.user_id) AS members,
               (SELECT COUNT(*) FROM click_events c JOIN rec_serves s2 ON s2.serve_id = c.serve_id
                WHERE s2.ab_arm = s.ab_arm) AS clicks
        FROM rec_serves s WHERE s.ab_arm IN ('v7', 'control') GROUP BY s.ab_arm""").fetchall()
    arm = {r[0]: {"serves": r[1], "members": r[2], "clicks": r[3]} for r in rows}
    for a in arm.values():
        a["cps"] = a["clicks"] / a["serves"]
        a["cpm"] = a["clicks"] / a["members"]
    d_cps = 100 * (arm["v7"]["cps"] / arm["control"]["cps"] - 1)
    d_cpm = 100 * (arm["v7"]["cpm"] / arm["control"]["cpm"] - 1)
    tot = arm["v7"]["serves"] + arm["control"]["serves"]
    z = (arm["v7"]["serves"] - tot / 2) / math.sqrt(tot / 4)
    tot_m = arm["v7"]["members"] + arm["control"]["members"]
    z_m = (arm["v7"]["members"] - tot_m / 2) / math.sqrt(tot_m / 4)
    (root / "reports/ab/AB-1182_readout.md").write_text(f"""# AB-1182: ranker v7 vs v6 (home row)

Assignment: member, 50/50, among sessions not hashed into the exploration stream. Window: the A/B period in the
current extract.

| Arm | Members | Responses | Clicks | Clicks per response |
|---|---:|---:|---:|---:|
| control (v6) | {arm['control']['members']:,} | {arm['control']['serves']:,} | {arm['control']['clicks']:,} | {arm['control']['cps']:.4f} |
| v7 | {arm['v7']['members']:,} | {arm['v7']['serves']:,} | {arm['v7']['clicks']:,} | {arm['v7']['cps']:.4f} |

- Clicks per response: **{d_cps:+.1f}%** for v7.
- Clicks per member: **{d_cpm:+.1f}%** for v7.
- Sample ratio checks: responses z = {z:+.1f}, members z = {z_m:+.1f}. Both inside the platform's alerting band, so
  the read-out was released without a warning.

Experimentation's note: the arms ran concurrently over the same members and devices, so the comparison is the
straightforward one. The result disagrees in sign with the offline gate run on the same ranker.
""")

    # June notebook: IPS with the logged propensity field, item-anywhere matching
    cand = {}
    for serve_id, item_id, s6, s7, s7pd, reason in con.execute(
            "SELECT serve_id, item_id, score_v6, score_v7, score_v7_pd, filter_reason FROM rec_candidates"):
        if reason is None:
            cand.setdefault(serve_id, []).append((item_id, s6, s7, s7pd))
    clicks_by_serve = {}
    for serve_id, item_id in con.execute("SELECT serve_id, item_id FROM click_events"):
        clicks_by_serve.setdefault(serve_id, []).append(item_id)
    n_expl_responses = con.execute("SELECT COUNT(*) FROM rec_serves WHERE stream = 'explore_shuffle'").fetchone()[0]
    raw_max, w_sum, n_serves = 0.0, 0.0, 0
    num = {"v6": 0.0, "v7": 0.0, "v7_pd": 0.0}
    for serve_id, prop, K, stream in con.execute(
            "SELECT serve_id, propensity, candidate_count, stream FROM rec_serves WHERE stream = 'explore_shuffle'"):
        rows = cand.get(serve_id)
        if rows is None:
            continue
        n_serves += 1
        w = 1.0 / max(prop, 1e-4)
        raw_max = max(raw_max, 1.0 / max(prop, 1e-12))
        w_sum += w
        clicked = clicks_by_serve.get(serve_id, [])
        if not clicked:
            continue
        for pol, col in (("v6", 1), ("v7", 2), ("v7_pd", 3)):
            top = {r[0] for r in sorted(rows, key=lambda r: -r[col])[:5]}
            num[pol] += w * sum(1 for it in clicked if it in top)
    est = {p: num[p] / w_sum for p in num}
    lift = {p: 100 * (est[p] / est["v6"] - 1) for p in ("v7", "v7_pd")}

    nb = {
        "cells": [
            {"cell_type": "markdown", "metadata": {}, "source": [
                "# IPS on the exploration stream (spike)\n", "\n",
                "Data Science intern, June 2026. Inverse propensity weighting with the `propensity` column on the\n",
                "exploration responses, then the same thing with the weights clipped and self-normalised.\n"]},
            {"cell_type": "code", "execution_count": 1, "metadata": {}, "outputs": [
                {"name": "stdout", "output_type": "stream", "text": [
                    f"exploration responses: {n_expl_responses}\n",
                    f"max raw weight 1/propensity: {raw_max:.3e}\n",
                    "raw IPS estimate of clicks per response: 1.7e+04   <- unusable\n"]}],
             "source": ["w = 1.0 / serves.propensity\n",
                        "print('max raw weight', w.max())\n",
                        "print('raw IPS', (w * clicks_per_serve).sum() / len(serves))\n"]},
            {"cell_type": "markdown", "metadata": {}, "source": [
                "The raw weights explode, which is expected with a slate probability. Clipping the weights and\n",
                "self-normalising gives something usable:\n"]},
            {"cell_type": "code", "execution_count": 2, "metadata": {}, "outputs": [
                {"name": "stdout", "output_type": "stream", "text": [
                    "clipped, self-normalised, clicks on titles each ranker would have shown:\n",
                    f"  v6     {est['v6']:.4f}\n", f"  v7     {est['v7']:.4f}   ({lift['v7']:+.1f}%)\n",
                    f"  v7_pd  {est['v7_pd']:.4f}   ({lift['v7_pd']:+.1f}%)\n"]}],
             "source": ["w = 1.0 / serves.propensity.clip(lower=1e-4)\n",
                        "for pol in ('v6', 'v7', 'v7_pd'):\n",
                        "    hit = clicks.item_id.isin(top5[pol])\n",
                        "    print(pol, (w * hit.groupby(level=0).sum()).sum() / w.sum())\n"]},
            {"cell_type": "markdown", "metadata": {}, "source": [
                "The ordering agrees with the offline gate, which is reassuring. The absolute level is not the\n",
                "same thing as the gate's CTR@5, so I have not tried to reconcile them. Parked: the gate is\n",
                "simpler and the team already trusts it.\n"]},
        ],
        "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"}},
        "nbformat": 4, "nbformat_minor": 5}
    (root / "notebooks/2026-06-12_ips_spike.ipynb").write_text(json.dumps(nb, indent=1) + "\n")


if __name__ == "__main__":
    main(Path(sys.argv[1] if len(sys.argv) > 1 else "."))
