"""Monthly lead-score evaluation run."""
from __future__ import annotations

import logging
import sys
from datetime import date

from lead_eval import __version__
from lead_eval.cohort import build_cohort, evaluation_window
from lead_eval.config import Config
from lead_eval.metrics import compute_metrics
from lead_eval.report import write_cohort, write_report
from lead_eval.sources import load_revops

log = logging.getLogger("lead_eval")


def run_evaluation(cfg: Config, as_of: date) -> dict:
    if not log.handlers:
        h = logging.StreamHandler(sys.stdout)
        h.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
        log.addHandler(h)
        log.setLevel(logging.INFO)
    src = load_revops(cfg.revops_db)
    window_start, matured_before = evaluation_window(cfg, as_of)
    cohort = build_cohort(src, cfg, as_of)
    log.info("lead_eval %s as_of=%s model=%s window=[%s, %s] cohort=%d converted=%d", __version__, as_of,
             cfg.champion_model, window_start.date(), matured_before, len(cohort), int(cohort["label"].sum()))
    write_cohort(cohort, cfg.artifacts_dir / "eval_cohort.csv")
    metrics = compute_metrics(cohort, cfg.n_bins, cfg.target_conversion_rate)
    report = {"as_of": as_of.isoformat(), "model_version": cfg.champion_model, "code_version": __version__,
              "window_start": str(window_start), "matured_before": str(matured_before), **metrics}
    path = write_report(cfg.reports_dir, as_of, report)
    log.info("roc_auc=%.4f top_decile_lift=%.2f recommended_threshold=%s -> %s", metrics["roc_auc"],
             metrics["top_decile_lift"], metrics["recommended_threshold"], path.relative_to(cfg.root))
    return report
