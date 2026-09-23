"""Generate the G44 mutation suite.

Each mutation is the oracle solution with one defect applied by textual substitution. M00 is
behaviour-preserving and must still score 1; every other mutation is a correct computation over a wrong
construction of the evidence, the weights or the population, and must score 0.
"""
import pathlib
import shutil

ROOT = pathlib.Path(__file__).resolve().parents[2]
SRC = ROOT / "candidates/g44-screening-precision/solution/screen_perf"
OUT = pathlib.Path(__file__).resolve().parent / "mutations"

LAB = (SRC / "labels.py").read_text()
MET = (SRC / "metrics.py").read_text()
CLI = (SRC / "cli.py").read_text()
FILES = {"labels.py": LAB, "metrics.py": MET, "cli.py": CLI}

EDITS = [
    ("M00_equivalent_rate_algebra", "metrics.py",
     "    d = se * prevalence + (1.0 - sp) * (1.0 - prevalence)\n    return se * prevalence / d if d else 0.0",
     "    tp = se * prevalence\n    fp = (1.0 - sp) * (1.0 - prevalence)\n"
     "    return 1.0 / (1.0 + fp / tp) if tp else 0.0", 1),
    ("M01_sample_weights_ignored", "labels.py",
     '    df["weight"] = df["review_source"].map({"QUEUE_FLAGGED": 1.0, "QUALITY_SAMPLE": float(n)})',
     '    df["weight"] = 1.0', 0),
    ("M02_ad_hoc_reviews_included", "labels.py",
     '    df = df[df["review_source"].isin(["QUEUE_FLAGGED", "QUALITY_SAMPLE"])]', '', 0),
    ("M03_pending_counted_as_legitimate", "labels.py",
     '    df = df[df["outcome"] != "PENDING"].copy()', '    df = df.copy()', 0),
    ("M04_benchmark_panel_rates", "cli.py",
     "    rev = labels.sample_reviews(warehouse)\n    c = metrics.weighted_confusion(rev)",
     "    rev = labels.sample_reviews(warehouse)\n"
     "    pan = labels.panel(warehouse).rename(columns={'label': 'outcome'})\n"
     "    pan['weight'] = 1.0\n"
     "    c = metrics.weighted_confusion(pan)", 0),
    ("M05_transport_skipped", "cli.py",
     "    contract = metrics.precision_at_rate(se, sp, merchant_rate)",
     "    contract = metrics.precision(c)", 0),
    ("M06_transport_at_own_book_rate", "cli.py",
     "    contract = metrics.precision_at_rate(se, sp, merchant_rate)",
     "    own = (c['tp'] + c['fn']) / (c['tp'] + c['fp'] + c['fn'] + c['tn'])\n"
     "    contract = metrics.precision_at_rate(se, sp, own)", 0),
    ("M07_rates_swapped", "cli.py",
     "    contract = metrics.precision_at_rate(se, sp, merchant_rate)",
     "    contract = metrics.precision_at_rate(sp, se, merchant_rate)", 0),
    ("M08_flag_rate_as_prevalence", "cli.py",
     "    contract = metrics.precision_at_rate(se, sp, merchant_rate)",
     "    contract = metrics.precision_at_rate(se, sp, float((txn['screen_decision'] == 'FLAG').mean()))", 0),
    ("M09_flagged_counted_from_reviews", "cli.py",
     '        "flagged_transactions": int((txn["screen_decision"] == "FLAG").sum()),',
     '        "flagged_transactions": int((rev["screen_decision"] == "FLAG").sum()),', 0),
    ("M10_npv_reported_as_precision", "cli.py",
     "    contract = metrics.precision_at_rate(se, sp, merchant_rate)",
     "    p = merchant_rate\n    contract = (sp * (1 - p)) / (sp * (1 - p) + (1 - se) * p)", 0),
    ("M11_hardcoded_sampling_fraction", "labels.py",
     '    n = int(terms(db)["quality_sample_one_in"])', '    n = 10', 0),
]


def main():
    if OUT.exists():
        shutil.rmtree(OUT)
    expected = {}
    for mid, fname, old, new, reward in EDITS:
        d = OUT / mid
        d.mkdir(parents=True)
        text = FILES[fname]
        assert text.count(old) == 1, f"{mid}: anchor not unique in {fname}"
        (d / fname).write_text(text.replace(old, new))
        expected[mid] = reward
    (OUT / "expected.txt").write_text("".join(f"{k} {v}\n" for k, v in sorted(expected.items())))
    print(f"wrote {len(expected)} mutations to {OUT}")


if __name__ == "__main__":
    main()
