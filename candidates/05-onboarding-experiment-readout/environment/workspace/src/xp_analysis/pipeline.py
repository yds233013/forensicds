"""Experiment readout run."""
from __future__ import annotations

import logging
import sys
from datetime import date

from xp_analysis import __version__
from xp_analysis.config import Config
from xp_analysis.estimator import estimate
from xp_analysis.report import write_readout, write_units
from xp_analysis.sources import load_product
from xp_analysis.units import build_units

log = logging.getLogger("xp_analysis")


def run_readout(cfg: Config, analysis_date: date) -> dict:
    if not log.handlers:
        h = logging.StreamHandler(sys.stdout)
        h.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
        log.addHandler(h)
        log.setLevel(logging.INFO)
    src = load_product(cfg.product_db, cfg.experiment_id)
    units = build_units(src, cfg, analysis_date)
    write_units(units, cfg.artifacts_dir / f"{cfg.experiment_id}_units.csv")
    est = estimate(units, cfg.z, cfg.treatment_share)
    readout = {"experiment_id": cfg.experiment_id, "analysis_date": analysis_date.isoformat(), "code_version": __version__,
               **est}
    path = write_readout(cfg.reports_dir, cfg.experiment_id, analysis_date, readout)
    log.info("xp_analysis %s %s analysis_date=%s units=%d/%d effect=%+.4f ci=[%+.4f, %+.4f] decision=%s srm_p=%.2g -> %s",
             __version__, cfg.experiment_id, analysis_date, est["n_units_control"], est["n_units_treatment"], est["effect"],
             est["ci_low"], est["ci_high"], est["decision"], est["srm_p_value"], path.relative_to(cfg.root))
    if est["srm_p_value"] < 0.001:
        log.warning("SRM check p=%.2g (exposure-based unit counts are noisy, XPP-19)", est["srm_p_value"])
    return readout
