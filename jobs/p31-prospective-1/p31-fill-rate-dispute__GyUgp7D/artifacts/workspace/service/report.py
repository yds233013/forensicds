"""Writes out/readout.json for the category service-level report."""
import json
import os

from service import metrics


def write_report(db_path, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    con = metrics.connect(db_path)
    try:
        lo, hi = metrics.period(con)
        rate, lines, filled = metrics.fill_rate_pct(con, lo, hi)
        per_account, below = {}, 0
        for a in metrics.accounts(con):
            r, n, f = metrics.fill_rate_pct(con, lo, hi, a["account_id"])
            if r is None:
                continue
            per_account[a["account_id"]] = round(r, 2)
            if r < a["service_floor_pct"]:
                below += 1
        readout = {
            "period": [lo, hi],
            "fill_rate_contract_pct": round(rate, 2),
            "lines": lines,
            "lines_filled": filled,
            "account_fill_pct": per_account,
            "accounts_below_floor": below,
        }
        with open(os.path.join(out_dir, "readout.json"), "w") as fh:
            json.dump(readout, fh, indent=2, sort_keys=True)
            fh.write("\n")
    finally:
        con.close()
