"""Build the semantic layer: run SQL models in order against the warehouse extract, then export board extracts."""
from __future__ import annotations

import csv
import logging
import sqlite3
import sys
from datetime import date

from metrics_layer import __version__
from metrics_layer.calendar import reporting_quarters
from metrics_layer.config import Config

log = logging.getLogger("metrics_layer")
EXPORTS = {"retention_quarterly": "retention_quarterly.csv", "retention_by_segment": "retention_by_segment.csv"}


def build(cfg: Config, as_of: date) -> None:
    if not log.handlers:
        h = logging.StreamHandler(sys.stdout)
        h.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
        log.addHandler(h)
        log.setLevel(logging.INFO)
    cfg.analytics_db.parent.mkdir(parents=True, exist_ok=True)
    cfg.analytics_db.unlink(missing_ok=True)
    con = sqlite3.connect(f"file:{cfg.analytics_db}", uri=True)
    con.execute(f"ATTACH DATABASE 'file:{cfg.warehouse_db}?mode=ro' AS src")
    con.execute("CREATE TABLE dim_quarters (quarter TEXT PRIMARY KEY, start_date TEXT NOT NULL, end_date TEXT NOT NULL)")
    con.executemany("INSERT INTO dim_quarters VALUES (?,?,?)", reporting_quarters(as_of, cfg.n_quarters))
    for model in sorted(cfg.models_dir.glob("*.sql")):
        con.executescript(model.read_text())
        log.info("built %s", model.stem)
    con.commit()
    cfg.board_dir.mkdir(parents=True, exist_ok=True)
    for table, fname in EXPORTS.items():
        cur = con.execute(f"SELECT * FROM {table} ORDER BY 1, 2")
        with open(cfg.board_dir / fname, "w", newline="") as fh:
            w = csv.writer(fh)
            w.writerow([c[0] for c in cur.description])
            w.writerows(cur.fetchall())
    latest = con.execute("SELECT quarter, nrr, grr, logo_churn_rate FROM retention_quarterly ORDER BY quarter DESC LIMIT 1").fetchone()
    log.info("metrics_layer %s as_of=%s latest %s NRR=%.4f GRR=%.4f logo churn=%.4f", __version__, as_of, *latest)
    con.close()
