"""Generate the G42 mutation suite.

Each mutation is the oracle solution with one defect applied by textual substitution, so the mutant
differs from the oracle only in the stated way. M00 is behaviour-preserving and must still score 1.
Every other mutation is a correct computation over a wrong construction of the numerator, the
denominator or the aggregation, and must score 0.
"""
import pathlib
import shutil

ROOT = pathlib.Path(__file__).resolve().parents[2]
SRC = ROOT / "candidates/g42-contractor-safety-rate/solution/safety_rate"
OUT = pathlib.Path(__file__).resolve().parent / "mutations"

EXP = (SRC / "exposure.py").read_text()
CAS = (SRC / "cases.py").read_text()
CLI = (SRC / "cli.py").read_text()
FILES = {"exposure.py": EXP, "cases.py": CAS, "cli.py": CLI}

EDITS = [
    # behaviour-preserving: same quantities by a different route through pandas
    ("M00_equivalent_aggregation", "cli.py",
     '    total_hours = round(float(h["hours"].sum()), 2)',
     '    total_hours = round(float(h.groupby("site_id")["hours"].sum().sum()), 2)', 1),
    ("M01_payroll_hours", "exposure.py",
     '    return df[df["hour_type"] == "WORKED"]', '    return df', 0),
    ("M02_scheduled_hours", "exposure.py",
     '    return df[df["hour_type"] == "WORKED"]',
     '    df = df[df["hour_type"] == "WORKED"].copy()\n    df["hours"] = df["scheduled_hours"]\n    return df', 0),
    ("M03_agency_hours_dropped", "exposure.py",
     '    df = df[(df["work_date"] >= lo) & (df["work_date"] < hi)]',
     '    emp = pd.read_sql_query("SELECT worker_id FROM workers WHERE worker_type = \'EMPLOYEE\'", connect(db))\n'
     '    df = df[(df["work_date"] >= lo) & (df["work_date"] < hi) & df["worker_id"].isin(set(emp["worker_id"]))]', 0),
    ("M05_first_aid_counted", "cases.py",
     '    return df[df["classification"] == "RECORDABLE"]',
     '    return df[df["classification"].isin(["RECORDABLE", "FIRST_AID"])]', 0),
    ("M06_under_review_counted", "cases.py",
     '    return df[df["classification"] == "RECORDABLE"]',
     '    return df[df["classification"].isin(["RECORDABLE", "UNDER_REVIEW"])]', 0),
    ("M07_window_on_record_date", "cases.py",
     '    df["occurred_on"] = pd.to_datetime(df["occurred_on"])\n'
     '    df = df[(df["occurred_on"] >= lo) & (df["occurred_on"] < hi)]',
     '    df["recorded_on"] = pd.to_datetime(df["recorded_on"])\n'
     '    df = df[(df["recorded_on"] >= lo) & (df["recorded_on"] < hi)]', 0),
    ("M08_one_case_per_event", "cases.py",
     '    return df[df["classification"] == "RECORDABLE"]',
     '    return df[df["classification"] == "RECORDABLE"].drop_duplicates(subset=["event_id"])', 0),
    ("M09_headcount_x_2000", "cli.py",
     '    total_hours = round(float(h["hours"].sum()), 2)',
     '    total_hours = round(2000.0 * h["worker_id"].nunique(), 2)', 0),
    ("M10_mean_of_site_rates", "cli.py",
     '    readout = {',
     '    company = round(sum(r["rate"] for r in rows) / len(rows), 4) if rows else 0.0\n    readout = {', 0),
    ("M11_home_site_attribution", "cases.py",
     '    return df[df["classification"] == "RECORDABLE"]',
     '    wk = pd.read_sql_query("SELECT worker_id, home_site_id FROM workers", connect(db))\n'
     '    df = df.merge(wk, on="worker_id", how="left")\n'
     '    df["site_id"] = df["home_site_id"].fillna(df["site_id"])\n'
     '    return df[df["classification"] == "RECORDABLE"]', 0),
    ("M12_calendar_year_window", "exposure.py",
     '    end = pd.Timestamp(t["reporting_window_end"])\n    return end - pd.DateOffset(months=int(t["reporting_window_months"])), end',
     '    end = pd.Timestamp(t["reporting_window_end"])\n'
     '    return pd.Timestamp(year=end.year - 1, month=1, day=1), pd.Timestamp(year=end.year, month=1, day=1)', 0),
]

# M04 drops agency workers from both sides.
M04_CASES = '''    wk = pd.read_sql_query("SELECT worker_id, worker_type FROM workers", connect(db))
    df = df.merge(wk, on="worker_id", how="left")
    df = df[df["worker_type"] == "EMPLOYEE"]
    return df[df["classification"] == "RECORDABLE"]'''


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
    d = OUT / "M04_agency_excluded_entirely"
    d.mkdir(parents=True)
    agency_free_hours = EXP.replace(
        '    df = df[(df["work_date"] >= lo) & (df["work_date"] < hi)]',
        '    emp = pd.read_sql_query("SELECT worker_id FROM workers WHERE worker_type = \'EMPLOYEE\'", connect(db))\n'
        '    df = df[(df["work_date"] >= lo) & (df["work_date"] < hi) & df["worker_id"].isin(set(emp["worker_id"]))]')
    (d / "exposure.py").write_text(agency_free_hours)
    (d / "cases.py").write_text(CAS.replace('    return df[df["classification"] == "RECORDABLE"]', M04_CASES))
    expected["M04_agency_excluded_entirely"] = 0
    (OUT / "expected.txt").write_text("".join(f"{k} {v}\n" for k, v in sorted(expected.items())))
    print(f"wrote {len(expected)} mutations to {OUT}")


if __name__ == "__main__":
    main()
