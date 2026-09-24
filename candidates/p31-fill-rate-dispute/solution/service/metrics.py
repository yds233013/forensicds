"""The category fill rate, per Schedule 2 of the customer supply agreement.

A line is filled where delivered quantity is not less than confirmed quantity. Lines the customer cancelled are
excluded. Lines are assigned to the period by requested delivery date. Returns are not a fill-rate event and are
not deducted.
"""
import sqlite3

REPORT_WEEKS = 13


def connect(db_path):
    con = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    return con


def period(con):
    row = con.execute("SELECT MIN(requested_delivery_date) AS lo FROM order_lines").fetchone()
    lo = row["lo"]
    y, m, d = (int(x) for x in lo.split("-"))
    from datetime import date, timedelta
    start = date(y, m, d)
    return start.isoformat(), (start + timedelta(days=7 * REPORT_WEEKS)).isoformat()


def fill_rate_pct(con, lo, hi, account_id=None):
    where = ("WHERE cancelled_by_customer = 0 AND requested_delivery_date >= ? "
             "AND requested_delivery_date < ?")
    args = [lo, hi]
    if account_id:
        where += " AND account_id = ?"
        args.append(account_id)
    row = con.execute(
        "SELECT COUNT(confirmed_qty) AS lines, "
        "       SUM(CASE WHEN delivered_qty >= confirmed_qty THEN 1 ELSE 0 END) AS filled "
        f"FROM order_lines {where}", args).fetchone()
    if not row["lines"]:
        return None, 0, 0
    return 100.0 * row["filled"] / row["lines"], row["lines"], row["filled"]


def accounts(con):
    return con.execute("SELECT account_id, service_floor_pct FROM accounts ORDER BY account_id").fetchall()
