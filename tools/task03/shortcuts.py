#!/usr/bin/env python3
"""Anti-gaming mutation suite for Task 03 (lead-score evaluation population).

Each case starts from the incident-time workspace inside the task image, applies one repair attempt, re-runs the
evaluation, then runs the real tests/test.sh. Shortcuts and overfits must score 0; independently written correct
repairs must score 1.

usage: shortcuts.py --docker IMAGE [--only NAME ...] [--jobs N] [--report PATH]
       shortcuts.py --apply NAME --task /task      (internal, inside the container)
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import sqlite3
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
TASK = (HERE.parents[1] if len(HERE.parents) > 1 else HERE) / "candidates/03-lead-score-evaluation"
WS = Path("/workspace")
COHORT = WS / "src/lead_eval/cohort.py"

HEADER = '''"""Evaluation cohort (mutation variant)."""
from __future__ import annotations

from datetime import date

import pandas as pd

from lead_eval.config import Config
from lead_eval.sources import RevOps

COHORT_COLUMNS = ["lead_id", "created_at", "source", "score", "label"]


def evaluation_window(cfg: Config, as_of: date):
    as_of_ts = pd.Timestamp(as_of)
    matured_before = as_of_ts - pd.Timedelta(days=cfg.outcome_window_days)
    return matured_before - pd.Timedelta(days=cfg.eval_window_days), matured_before


def first_event(ev):
    return ev.sort_values(["lead_id", "routed_at", "routing_event_id"], kind="mergesort").drop_duplicates("lead_id")


def last_event(ev):
    return ev.sort_values(["lead_id", "routed_at", "routing_event_id"], kind="mergesort").drop_duplicates("lead_id", keep="last")


def worked_ids(src, as_of):
    a = src.activities[src.activities["activity_at"] < pd.Timestamp(as_of)]
    return set(a["lead_id"])


def build_cohort(src: RevOps, cfg: Config, as_of: date) -> pd.DataFrame:
    window_start, matured_before = evaluation_window(cfg, as_of)
    leads = src.leads[src.leads["intake_status"] == "accepted"]
    leads = leads[(leads["created_at"] >= window_start) & (leads["created_at"] <= matured_before)]
    ev = src.routing_events
#SELECT#
    scores = src.scores[src.scores["model_version"] == #MODEL#][["lead_id", "score"]]
    cohort = leads.merge(scores, on="lead_id", how="inner", validate="one_to_one")
#LABEL#
    return cohort.sort_values("lead_id").reset_index(drop=True)[COHORT_COLUMNS]
'''
INTAKE_HOLDOUT = '''    f = first_event(ev)
    leads = leads[leads["lead_id"].isin(set(f.loc[f["policy"] == "exploration_holdout", "lead_id"]))]'''
LIFECYCLE_LABEL = '''    out = src.lifecycle[["lead_id", "converted_60d"]]
    cohort = cohort.merge(out, on="lead_id", how="left")
    cohort["label"] = cohort["converted_60d"].fillna(0).astype(int)'''


def cohort_variant(select: str = INTAKE_HOLDOUT, label: str = LIFECYCLE_LABEL, model: str = "cfg.champion_model") -> None:
    COHORT.write_text(HEADER.replace("#SELECT#", select).replace("#LABEL#", label).replace("#MODEL#", model))


def patch(path: Path, old: str, new: str) -> None:
    s = path.read_text()
    assert old in s, f"anchor not found in {path}: {old[:60]}"
    path.write_text(s.replace(old, new, 1))


# ------------------------------------------------------------------------------------------------ controls


def nop():
    """No change (Nop agent)."""


def oracle():
    """Reference solution."""
    shutil.copyfile(TASK / "solution/lead_eval/cohort.py", COHORT)


def alt_correct_sql():
    """Independent correct repair: cohort built in SQLite (window function for intake policy, labels from conversions)."""
    COHORT.write_text('''"""Evaluation cohort built in SQL."""
import sqlite3
from datetime import date, timedelta

import pandas as pd

COHORT_COLUMNS = ["lead_id", "created_at", "source", "score", "label"]


def evaluation_window(cfg, as_of):
    a = pd.Timestamp(as_of)
    m = a - pd.Timedelta(days=cfg.outcome_window_days)
    return m - pd.Timedelta(days=cfg.eval_window_days), m


def build_cohort(src, cfg, as_of: date) -> pd.DataFrame:
    start, matured = evaluation_window(cfg, as_of)
    con = sqlite3.connect(f"file:{cfg.revops_db}?mode=ro", uri=True)
    df = pd.read_sql_query("""
        WITH intake AS (
          SELECT lead_id, policy, ROW_NUMBER() OVER (PARTITION BY lead_id ORDER BY routed_at, routing_event_id) rn
          FROM routing_events)
        SELECT l.lead_id, l.created_at, l.source, s.score,
               EXISTS (SELECT 1 FROM conversions c WHERE c.lead_id = l.lead_id
                       AND (julianday(c.closed_won_at) - julianday(l.created_at)) * 86400 <= ? * 86400) AS label
        FROM leads l
        JOIN intake i ON i.lead_id = l.lead_id AND i.rn = 1 AND i.policy = 'exploration_holdout'
        JOIN lead_scores s ON s.lead_id = l.lead_id AND s.model_version = ?
        WHERE l.intake_status = 'accepted' AND l.created_at >= ? AND l.created_at <= ?
        ORDER BY l.lead_id""", con, params=(cfg.outcome_window_days, cfg.champion_model,
                                            start.strftime("%Y-%m-%d %H:%M:%S"), matured.strftime("%Y-%m-%d %H:%M:%S")))
    con.close()
    df["created_at"] = pd.to_datetime(df["created_at"])
    df["label"] = df["label"].astype(int)
    return df[COHORT_COLUMNS]
''')


def alt_correct_python():
    """Independent correct repair: plain-Python loops over routing events and conversions."""
    COHORT.write_text('''"""Evaluation cohort (plain Python)."""
from datetime import date, datetime, timedelta

import pandas as pd

COHORT_COLUMNS = ["lead_id", "created_at", "source", "score", "label"]


def evaluation_window(cfg, as_of):
    a = pd.Timestamp(as_of)
    m = a - pd.Timedelta(days=cfg.outcome_window_days)
    return m - pd.Timedelta(days=cfg.eval_window_days), m


def build_cohort(src, cfg, as_of: date) -> pd.DataFrame:
    start, matured = evaluation_window(cfg, as_of)
    first = {}
    for r in sorted(src.routing_events.itertuples(index=False), key=lambda r: (r.lead_id, r.routed_at, r.routing_event_id)):
        first.setdefault(r.lead_id, r.policy)
    score = {r.lead_id: r.score for r in src.scores.itertuples(index=False) if r.model_version == cfg.champion_model}
    won = {}
    for r in src.conversions.itertuples(index=False):
        won.setdefault(r.lead_id, []).append(r.closed_won_at)
    rows = []
    for r in src.leads.itertuples(index=False):
        if r.intake_status != "accepted" or not (start <= r.created_at <= matured) or first.get(r.lead_id) != "exploration_holdout":
            continue
        label = int(any(t - r.created_at <= pd.Timedelta(days=cfg.outcome_window_days) for t in won.get(r.lead_id, [])))
        rows.append((r.lead_id, r.created_at, r.source, score[r.lead_id], label))
    return pd.DataFrame(rows, columns=COHORT_COLUMNS).sort_values("lead_id").reset_index(drop=True)
''')


# ------------------------------------------------------------------------------------------------ shortcuts


def worked_leads_only():
    """Evaluate only leads an SDR actually worked (outcomes 'observed under treatment')."""
    cohort_variant('''    leads = leads[leads["lead_id"].isin(worked_ids(src, as_of))]''')


def holdout_per_protocol():
    """Intake holdout, but only holdout leads an SDR reached."""
    cohort_variant(INTAKE_HOLDOUT + '''
    leads = leads[leads["lead_id"].isin(worked_ids(src, as_of))]''')


def current_sdr_queue():
    """Leads whose current lifecycle queue is the SDR queue (routed, holdout and claimed leads)."""
    cohort_variant('''    q = src.lifecycle.loc[src.lifecycle["current_queue"] == "sdr_inbound", "lead_id"]
    leads = leads[leads["lead_id"].isin(set(q))]''')


def above_threshold_only():
    """Only leads routed on score (score >= router threshold at intake): 'evaluate where the model decides'."""
    cohort_variant('''    f = first_event(ev)
    leads = leads[leads["lead_id"].isin(set(f.loc[f["policy"] == "score_threshold", "lead_id"]))]''')


def below_threshold_sdr_reconstruction():
    """Reconstruct the random slice as intake SDR leads scoring below the router threshold."""
    cohort_variant('''    f = first_event(ev)
    f = f[(f["queue"] == "sdr_inbound") & (f["threshold"].notna())]
    s = src.scores[src.scores["model_version"] == cfg.champion_model].set_index("lead_id")["score"]
    f = f[f["lead_id"].map(s) < f["threshold"]]
    leads = leads[leads["lead_id"].isin(set(f["lead_id"]))]''')


def qualified_as_label():
    """Intake holdout with the SDR 'qualified' flag as the outcome (a downstream operational decision)."""
    cohort_variant(label='''    out = src.lifecycle[["lead_id", "qualified"]]
    cohort = cohort.merge(out, on="lead_id", how="left")
    cohort["label"] = cohort["qualified"].fillna(0).astype(int)''')


def sales_led_conversions_only():
    """Intake holdout, but self-serve purchases are not counted as conversions."""
    cohort_variant(label='''    c = src.conversions[src.conversions["channel"] == "sales_led"].merge(leads[["lead_id", "created_at"]], on="lead_id")
    won = set(c.loc[(c["closed_won_at"] - c["created_at"]) <= pd.Timedelta(days=cfg.outcome_window_days), "lead_id"])
    cohort["label"] = cohort["lead_id"].isin(won).astype(int)''')


def holdout_without_maturity():
    """Intake holdout, but immature leads (outcome window still open) are evaluated too."""
    cohort_variant(INTAKE_HOLDOUT.replace("    f = first_event(ev)", '''    leads = src.leads[(src.leads["intake_status"] == "accepted") & (src.leads["created_at"] >= window_start)
                      & (src.leads["created_at"] < pd.Timestamp(as_of))]
    f = first_event(ev)'''))


def challenger_scores():
    """Intake holdout scored with the shadow challenger where available."""
    cohort_variant(INTAKE_HOLDOUT)
    patch(COHORT, '''    cohort = leads.merge(scores, on="lead_id", how="inner", validate="one_to_one")''',
          '''    ch = src.scores[src.scores["model_version"] == "lsm-3.3-shadow"][["lead_id", "score"]].rename(columns={"score": "ch"})
    cohort = leads.merge(scores, on="lead_id", how="inner", validate="one_to_one").merge(ch, on="lead_id", how="left")
    cohort["score"] = cohort["ch"].fillna(cohort["score"])''')


def ipw_worked_population():
    """Worked leads re-weighted by inverse routing propensity (holdout share for sub-threshold leads) in the metrics."""
    worked_leads_only()
    m = WS / "src/lead_eval/metrics.py"
    patch(m, '''    y = cohort["label"].to_numpy()
    s = cohort["score"].to_numpy()''', '''    y = cohort["label"].to_numpy()
    s = cohort["score"].to_numpy()
    w = np.where(s < 0.22, 10.0, 1.0)''')
    patch(m, '''        "roc_auc": float(roc_auc_score(y, s)),''', '''        "roc_auc": float(roc_auc_score(y, s, sample_weight=w)),''')
    patch(m, '''    overall = float(y.mean())''', '''    overall = float(np.average(y, weights=np.where(s < 0.22, 10.0, 1.0)))''')


def change_target_rate():
    """Leave the population; lower the target conversion rate so the threshold recommendation looks conservative."""
    cfg = WS / "config/evaluation.toml"
    cfg.write_text(cfg.read_text().replace("target_conversion_rate = 0.08", "target_conversion_rate = 0.12"))


def patch_report_numbers():
    """Cohort unchanged; report metrics recomputed on the intake holdout and written over the report."""
    p = WS / "src/lead_eval/pipeline.py"
    patch(p, '''    metrics = compute_metrics(cohort, cfg.n_bins, cfg.target_conversion_rate)''',
          '''    ev = src.routing_events.sort_values(["lead_id", "routed_at", "routing_event_id"]).drop_duplicates("lead_id")
    hold = cohort[cohort["lead_id"].isin(set(ev.loc[ev["policy"] == "exploration_holdout", "lead_id"]))]
    metrics = compute_metrics(hold, cfg.n_bins, cfg.target_conversion_rate)''')


def edit_source_outcomes():
    """Edit data/revops.db: remove lifecycle and conversion rows for nurture leads so they drop out."""
    con = sqlite3.connect(WS / "data/revops.db")
    con.execute("DELETE FROM lead_lifecycle WHERE current_queue = 'nurture'")
    con.execute("UPDATE leads SET intake_status = 'rejected_duplicate' WHERE lead_id NOT IN (SELECT lead_id FROM lead_lifecycle)")
    con.commit()
    con.close()


# ------------------------------------------------------------------------------------------------ overfits


def overfit_latest_routing_policy():
    """Holdout identified by the lead's latest routing event (visible extract has no re-routed holdout leads)."""
    cohort_variant('''    f = last_event(ev)
    leads = leads[leads["lead_id"].isin(set(f.loc[f["policy"] == "exploration_holdout", "lead_id"]))]''')


def overfit_visible_router_versions():
    """Intake holdout restricted to the router versions present in this extract."""
    cohort_variant(INTAKE_HOLDOUT.replace('f["policy"] == "exploration_holdout"',
                                          '(f["policy"] == "exploration_holdout") & f["router_version"].isin(["router-2025.11", "router-2026.06"])'))


def overfit_hardcoded_lead_ids():
    """Hard-coded list of this extract's holdout lead ids."""
    con = sqlite3.connect(WS / "data/revops.db")
    ids = sorted({r[0] for r in con.execute("SELECT lead_id FROM routing_events WHERE policy = 'exploration_holdout'")})
    con.close()
    cohort_variant(f'''    leads = leads[leads["lead_id"].isin({set(ids)!r})]''')


CONTROLS = [(nop, 0), (oracle, 1), (alt_correct_sql, 1), (alt_correct_python, 1)]
SHORTCUTS = [worked_leads_only, holdout_per_protocol, current_sdr_queue, above_threshold_only,
             below_threshold_sdr_reconstruction, qualified_as_label, sales_led_conversions_only, holdout_without_maturity,
             challenger_scores, ipw_worked_population, change_target_rate, patch_report_numbers, edit_source_outcomes,
             overfit_latest_routing_policy, overfit_visible_router_versions, overfit_hardcoded_lead_ids]
PLAN = CONTROLS + [(f, 0) for f in SHORTCUTS]


def run_docker(fn, expected, image) -> dict:
    script = (
        "set -e; "
        f"python /tools/shortcuts.py --apply {fn.__name__} --task /task; "
        "find /workspace/src -name __pycache__ -prune -exec rm -rf {} +; "
        "(cd /workspace && python -m lead_eval run --config config/evaluation.toml > /tmp/agent_run.log 2>&1 || true); "
        "mkdir -p /tests /logs/verifier; cp -r /task/tests/. /tests/; "
        "bash /tests/test.sh > /tmp/verifier.log 2>&1; "
        "echo REWARD=$(cat /logs/verifier/reward.txt); "
        "grep -E '[0-9]+ (passed|failed)' /tmp/verifier.log | tail -1; grep '^FAILED' /tmp/verifier.log || true"
    )
    p = subprocess.run(["docker", "run", "--rm", "--cpus", "2", "-v", f"{TASK}:/task:ro", "-v", f"{HERE}:/tools:ro", image,
                        "bash", "-c", script], capture_output=True, text=True)
    m = re.search(r"REWARD=(\d)", p.stdout)
    reward = int(m.group(1)) if m else -1
    summary = next((l.strip("= ") for l in p.stdout.splitlines() if " passed" in l or " failed" in l), p.stderr[-400:])
    return dict(name=fn.__name__, doc=(fn.__doc__ or "").strip(), expected=expected, reward=reward,
                ok=(expected is None or reward == expected), summary=summary, failed=re.findall(r"FAILED \S+::(\S+)", p.stdout))


def main():
    global TASK
    ap = argparse.ArgumentParser()
    ap.add_argument("--docker")
    ap.add_argument("--apply")
    ap.add_argument("--task")
    ap.add_argument("--only", nargs="*")
    ap.add_argument("--jobs", type=int, default=3)
    ap.add_argument("--report")
    a = ap.parse_args()
    if a.task:
        TASK = Path(a.task)
    if a.apply:
        dict((f.__name__, f) for f, _ in PLAN)[a.apply]()
        return
    plan = [(f, e) for f, e in PLAN if not a.only or f.__name__ in a.only]
    results = []
    with ThreadPoolExecutor(max_workers=a.jobs) as pool:
        for r in pool.map(lambda fe: run_docker(fe[0], fe[1], a.docker), plan):
            results.append(r)
            print(f"[{'OK ' if r['ok'] else 'BAD'}] {r['name']:40} reward={r['reward']} expected={r['expected']}  {r['summary']}", flush=True)
    if a.report:
        Path(a.report).write_text(json.dumps(results, indent=2))
    sys.exit(0 if all(r["ok"] for r in results) else 1)


if __name__ == "__main__":
    main()
