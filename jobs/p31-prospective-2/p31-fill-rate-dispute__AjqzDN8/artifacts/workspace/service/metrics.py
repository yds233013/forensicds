"""The category fill rate, per Schedule 2 of the customer supply agreement and supplier methodology.
"""
import sqlite3
from datetime import date, timedelta

REPORT_WEEKS = 13

def connect(db_path):
    con = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    return con

def get_period(con):
    row = con.execute("SELECT MIN(requested_delivery_date) AS lo FROM order_lines").fetchone()
    lo = row["lo"]
    y, m, d = (int(x) for x in lo.split("-"))
    start = date(y, m, d)
    return start.isoformat(), (start + timedelta(days=7 * REPORT_WEEKS)).isoformat()

def get_contract_fill_rate(con, lo, hi, basis='original', account_id=None):
    """
    Contractual fill rate: proportion of order lines filled.
    basis='original' uses confirmed_qty.
    basis='amended' uses amended_qty if not null, else confirmed_qty.
    """
    where = "WHERE cancelled_by_customer = 0 AND requested_delivery_date >= ? AND requested_delivery_date < ?"
    args = [lo, hi]
    if account_id:
        where += " AND account_id = ?"
        args.append(account_id)
    
    if basis == 'original':
        qty_col = "confirmed_qty"
    else:
        qty_col = "COALESCE(amended_qty, confirmed_qty)"
    
    # §7.2: If no confirmation (null confirmed_qty), treated as not filled.
    # delivered_qty >= confirmed_qty is false if confirmed_qty is NULL.
    # We use COUNT(*) for denominator to include lines with null confirmation.
    query = f"""
        SELECT 
            COUNT(*) as total_lines,
            SUM(CASE WHEN {qty_col} IS NOT NULL AND delivered_qty >= {qty_col} THEN 1 ELSE 0 END) as filled_lines
        FROM order_lines
        {where}
    """
    res = con.execute(query, args).fetchone()
    if not res or res['total_lines'] == 0:
        return None, 0, 0
    return 100.0 * res['filled_lines'] / res['total_lines'], res['total_lines'], res['filled_lines']

def get_supplier_fill_rate(con, lo, hi):
    """
    Supplier fill rate (case fill): (units delivered - units returned) / units requested.
    Period by despatch_date.
    """
    # Units ordered and delivered
    res = con.execute("""
        SELECT 
            SUM(requested_qty) as total_requested,
            SUM(delivered_qty) as total_delivered
        FROM order_lines
        WHERE cancelled_by_customer = 0
        AND despatch_date >= ? AND despatch_date < ?
    """, (lo, hi)).fetchone()
    
    if not res or not res['total_requested']:
        return 0.0
    
    # Returns against lines despatched in the period
    ret = con.execute("""
        SELECT SUM(r.return_qty) as total_returned
        FROM returns r
        JOIN order_lines o ON r.line_id = o.line_id
        WHERE o.cancelled_by_customer = 0
        AND o.despatch_date >= ? AND o.despatch_date < ?
    """, (lo, hi)).fetchone()
    
    total_returned = ret['total_returned'] or 0
    return 100.0 * (res['total_delivered'] - total_returned) / res['total_requested']

def get_bridge(con, lo, hi):
    """
    Calculates the bridge between contract rate and supplier rate.
    """
    # 1. Base Contract (Basis A)
    rate_contract, _, _ = get_contract_fill_rate(con, lo, hi, basis='original')
    
    # A. Aggregation: Line fill vs Case fill (Confirmed, Requested Date, No Returns)
    res = con.execute("""
        SELECT SUM(confirmed_qty) as n, SUM(CASE WHEN delivered_qty > confirmed_qty THEN confirmed_qty ELSE delivered_qty END) as f
        FROM order_lines
        WHERE cancelled_by_customer = 0 AND requested_delivery_date >= ? AND requested_delivery_date < ?
    """, (lo, hi)).fetchone()
    case_fill_confirmed = 100.0 * res['f'] / res['n']
    aggregation = case_fill_confirmed - rate_contract
    
    # B. Denominator: Confirmed vs Requested (Case fill, Requested Date, No Returns)
    res = con.execute("""
        SELECT SUM(requested_qty) as n, SUM(CASE WHEN delivered_qty > requested_qty THEN requested_qty ELSE delivered_qty END) as f
        FROM order_lines
        WHERE cancelled_by_customer = 0 AND requested_delivery_date >= ? AND requested_delivery_date < ?
    """, (lo, hi)).fetchone()
    case_fill_requested = 100.0 * res['f'] / res['n']
    denominator = case_fill_requested - case_fill_confirmed
    
    # C. Returns: (Case fill, Requested Date, Returns Deducted) - (Case fill, Requested Date, No Returns)
    res = con.execute("""
        SELECT SUM(requested_qty) as n, SUM(delivered_qty) as f
        FROM order_lines
        WHERE cancelled_by_customer = 0 AND requested_delivery_date >= ? AND requested_delivery_date < ?
    """, (lo, hi)).fetchone()
    ret = con.execute("""
        SELECT SUM(r.return_qty)
        FROM returns r
        JOIN order_lines o ON r.line_id = o.line_id
        WHERE o.cancelled_by_customer = 0 AND o.requested_delivery_date >= ? AND o.requested_delivery_date < ?
    """, (lo, hi)).fetchone()
    returns_qty = ret[0] or 0
    case_fill_requested_returns = 100.0 * (res['f'] - returns_qty) / res['n']
    returns_treatment = case_fill_requested_returns - case_fill_requested
    
    # D. Date Window: Supplier Final (Despatch Date) - Case fill (Requested Date, Returns Deducted)
    rate_supplier = get_supplier_fill_rate(con, lo, hi)
    date_window = rate_supplier - case_fill_requested_returns
    
    return {
        "aggregation": round(aggregation, 4),
        "denominator": round(denominator, 4),
        "returns_treatment": round(returns_treatment, 4),
        "date_window": round(date_window, 4),
        "other": 0.0
    }

def get_accounts(con):
    return con.execute("SELECT account_id, service_floor_pct FROM accounts ORDER BY account_id").fetchall()

def get_ticket_share(con):
    res = con.execute("""
        SELECT 
            COUNT(t.ticket_id) as total_tickets,
            SUM(CASE WHEN r.line_id IS NOT NULL THEN 1 ELSE 0 END) as tickets_with_returns
        FROM shortfall_tickets t
        LEFT JOIN (SELECT DISTINCT line_id FROM returns) r ON t.line_id = r.line_id
    """).fetchone()
    if not res or not res['total_tickets']:
        return 0.0
    return 100.0 * res['tickets_with_returns'] / res['total_tickets']
