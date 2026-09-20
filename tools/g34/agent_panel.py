"""Wrong-agent separation panel, scored against the FINAL frozen tolerance.

For every graded extract and every pre-registered wrong analysis A-H, report the error in
tolerance units (tau = TOL_MULTIPLIER x SE_REF).  A wrong analysis must exceed 1.0 on at
least one graded quantity for the extract to reject it.  Research/dev tool; no model call.
"""
from __future__ import annotations
import json, sys, tempfile
from pathlib import Path
import numpy as np, pandas as pd

ROOT = Path(__file__).resolve().parents[2] / "candidates" / "g34-fleet-reliability-gate"
sys.path.insert(0, str(ROOT / "tests"))
sys.path.insert(0, str(ROOT / "solution"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import world, scenarios                                            # noqa: E402
from fleet_reliability import history, estimate                    # noqa: E402
import agents                                                      # noqa: E402

QUANT = ("unplanned_failure_rate_36m", "overhaul_rate_36m", "retirement_rate_36m",
         "still_original_assembly_36m", "assembly_failure_rate_36m")
AGENT_KEY = {"unplanned_failure_rate_36m": "q1", "overhaul_rate_36m": "ovhl",
             "retirement_rate_36m": "ret", "still_original_assembly_36m": "surv",
             "assembly_failure_rate_36m": "q2"}
TRUTH_KEY = {"unplanned_failure_rate_36m": "q1_crude_failure_36", "overhaul_rate_36m": "cif_overhaul_36",
             "retirement_rate_36m": "cif_retirement_36", "still_original_assembly_36m": "survival_36",
             "assembly_failure_rate_36m": "q2_net_failure_36"}


def with_gap_age(df, db):
    """E_gap_censoring needs the age at the unit's first telemetry outage; the shipped history
    builder does not carry it, because handling that column is the agent's job, not the loader's."""
    con = history.connect(Path(db))
    try:
        tel = pd.read_sql_query("SELECT unit_id, MIN(gap_start) AS gap_start FROM telemetry_status"
                                " GROUP BY unit_id", con)
    finally:
        con.close()
    df = df.merge(tel, on="unit_id", how="left")
    df["gap_start"] = pd.to_datetime(df["gap_start"])
    df["first_gap_age"] = (df["gap_start"] - df["commissioned_on"]).dt.days / history.MONTH
    return df


def main():
    mult = scenarios.TOL_MULTIPLIER
    rows = []
    for name in scenarios.ALL_NAMES:
        spec = scenarios.by_name(name)
        d = tempfile.mkdtemp()
        w = world.build(spec)
        db = world.write_sqlite(w, d)
        truth = world.truth(w)
        df = with_gap_age(history.build(Path(db)), db)
        acc = agents.oracle(df)
        for label, fn in [("ACCEPTED_oracle", agents.oracle)] + sorted(agents.AGENTS.items()):
            est = fn(df)
            ratios = {}
            for q in QUANT:
                tau = mult * scenarios.SE_REF[name][q]
                # graded against the ACCEPTED estimator's value, which is what the verifier compares to
                ratios[q] = abs(est[AGENT_KEY[q]] - acc[AGENT_KEY[q]]) / tau
            worst = max(ratios.values())
            rows.append(dict(fixture=name, analysis=label, worst_ratio=round(worst, 2),
                             rejected=bool(worst > 1.0),
                             **{q: round(ratios[q], 2) for q in QUANT}))
        # sanity: accepted estimator vs latent truth on this very draw
        for q in QUANT:
            tau = mult * scenarios.SE_REF[name][q]
            rows.append(dict(fixture=name, analysis=f"_truthcheck:{q}",
                             worst_ratio=round(abs(acc[AGENT_KEY[q]] - truth[TRUTH_KEY[q]]) / tau, 2),
                             rejected=False))
    out = pd.DataFrame(rows)
    out.to_csv(Path(__file__).with_name("agent_panel.csv"), index=False)
    panel = out[~out.analysis.str.startswith("_truthcheck")]
    print(panel.pivot(index="analysis", columns="fixture", values="worst_ratio").to_string())
    print()
    tc = out[out.analysis.str.startswith("_truthcheck")]
    print("accepted-estimator-vs-latent-truth, worst over quantities:")
    print(tc.groupby("fixture").worst_ratio.max().to_string())
    wrong = panel[panel.analysis != "ACCEPTED_oracle"]
    bad = wrong.groupby("analysis").rejected.all()
    print("\nwrong analyses rejected by EVERY extract:", int(bad.sum()), "/", len(bad))
    if not bad.all():
        print("NOT rejected everywhere:", list(bad[~bad].index))


if __name__ == "__main__":
    main()
