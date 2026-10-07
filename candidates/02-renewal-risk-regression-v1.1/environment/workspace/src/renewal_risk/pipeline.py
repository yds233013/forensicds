"""Training run: examples -> features -> train -> evaluate -> report."""
from __future__ import annotations

import logging
import sys
import time
from datetime import date

import joblib
import pandas as pd

from renewal_risk import MODEL_VERSION, __version__
from renewal_risk.config import Config
from renewal_risk.examples import EXAMPLE_COLUMNS, build_examples
from renewal_risk.features.build import build_features
from renewal_risk.features.registry import FEATURE_COLUMNS
from renewal_risk.model.evaluate import evaluate
from renewal_risk.model.train import predict, train
from renewal_risk.reporting import write_report
from renewal_risk.sources.warehouse import load_warehouse

log = logging.getLogger("renewal_risk")


def _logging() -> None:
    if not log.handlers:
        h = logging.StreamHandler(sys.stdout)
        h.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
        log.addHandler(h)
        log.setLevel(logging.INFO)


def _write_csv(df: pd.DataFrame, path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    out = df.copy()
    for c in out.columns:
        if pd.api.types.is_datetime64_any_dtype(out[c]):
            out[c] = out[c].dt.strftime("%Y-%m-%d")
    out.to_csv(path, index=False)


def run_features(cfg: Config, as_of: date):
    _logging()
    wh = load_warehouse(cfg.warehouse_db)
    examples = build_examples(wh, cfg, as_of)
    log.info("examples: %d (train=%d eval=%d) as_of=%s", len(examples), (examples["split"] == "train").sum(),
             (examples["split"] == "eval").sum(), as_of)
    features = build_features(examples, wh)
    _write_csv(examples[EXAMPLE_COLUMNS], cfg.artifacts_dir / "examples.csv")
    _write_csv(features, cfg.artifacts_dir / "features.csv")
    log.info("features: %d rows x %d features -> %s", len(features), len(FEATURE_COLUMNS),
             (cfg.artifacts_dir / "features.csv").relative_to(cfg.root))
    return wh, examples, features


def run_training(cfg: Config, as_of: date) -> dict:
    t0 = time.time()
    _logging()
    log.info("renewal_risk %s (%s) training run as_of=%s", __version__, MODEL_VERSION, as_of)
    wh, examples, features = run_features(cfg, as_of)

    is_train = (examples["split"] == "train").to_numpy()
    model = train(features[is_train], examples.loc[is_train, "label"], cfg)
    (cfg.artifacts_dir / "model").mkdir(parents=True, exist_ok=True)
    joblib.dump(model, cfg.artifacts_dir / "model" / "renewal_risk.joblib")

    ev = examples[~is_train].reset_index(drop=True)
    preds = ev[["contract_id", "account_id", "prediction_date", "label"]].copy()
    preds["score"] = predict(model, features[~is_train].reset_index(drop=True))
    _write_csv(preds, cfg.artifacts_dir / "eval_predictions.csv")

    seg = preds.merge(wh.accounts[["account_id", "segment"]], on="account_id", how="left")
    metrics = evaluate(seg, cfg.calibration_bins)
    report = {
        "model_version": MODEL_VERSION,
        "code_version": __version__,
        "as_of": as_of.isoformat(),
        "n_train": int(is_train.sum()),
        "train_churn_rate": round(float(examples.loc[is_train, "label"].mean()), 6),
        "feature_columns": FEATURE_COLUMNS,
        **metrics,
    }
    path = write_report(cfg.reports_dir, as_of, report)
    log.info("eval: n=%d roc_auc=%.4f pr_auc=%.4f brier=%.4f -> %s", metrics["n_eval"], metrics["roc_auc"],
             metrics["pr_auc"], metrics["brier"], path.relative_to(cfg.root))
    log.info("done in %.1fs", time.time() - t0)
    return report
