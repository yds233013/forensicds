import sqlite3
from datetime import date, timedelta

REPORT_WEEKS = 13

def connect(db_path):
    con = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    return con

def period(con):
    row = con.execute("SELECT MIN(requested_delivery_date) AS lo FROM order_lines").fetchone()
    lo = row["lo"]
    y, m, d = (int(x) for x in lo.split("-"))
    start = date(y, m, d)
    return start.isoformat(), (start + timedelta(days=7 * REPORT_WEEKS)).isoformat()

def get_base_data(con, lo, hi):
    # Get all order lines
    lines = con.execute("SELECT * FROM order_lines WHERE cancelled_by_customer = 0").fetchall()
    
    # Get all returns
    returns = con.execute("SELECT line_id, SUM(return_qty) as qty FROM returns GROUP BY line_id").fetchall()
    return_map = {r['line_id']: r['qty'] for r in returns}
    
    # Get shortfall tickets
    tickets = con.execute("SELECT line_id, claim_type FROM shortfall_tickets").fetchall()
    ticket_list = [dict(t) for t in tickets]
    
    # Get accounts
    accounts = con.execute("SELECT account_id, service_floor_pct FROM accounts ORDER BY account_id").fetchall()
    account_list = [dict(a) for a in accounts]
    
    return lines, return_map, ticket_list, account_list

def calculate_contract_fill(lines, lo, hi, account_id=None, use_amended=False):
    # Filter by period (Requested Delivery Date) and account
    filtered = [l for l in lines if lo <= l['requested_delivery_date'] < hi]
    if account_id:
        filtered = [l for l in filtered if l['account_id'] == account_id]
    
    if not filtered:
        return None, 0, 0
    
    filled_count = 0
    for l in filtered:
        conf = l['confirmed_qty']
        if use_amended and l['amended_qty'] is not None:
            conf = l['amended_qty']
        
        # §7.2: If no confirmation, treated as not filled.
        if conf is None:
            continue
            
        if l['delivered_qty'] >= conf:
            filled_count += 1
            
    return 100.0 * filled_count / len(filtered), len(filtered), filled_count

def calculate_supplier_fill(lines, return_map, lo, hi):
    # Filter by period (Despatch Date)
    filtered = [l for l in lines if l['despatch_date'] and lo <= l['despatch_date'] < hi]
    
    if not filtered:
        return 0.0
    
    total_requested = sum(l['requested_qty'] for l in filtered)
    total_delivered = sum(l['delivered_qty'] for l in filtered)
    total_returned = sum(return_map.get(l['line_id'], 0) for l in filtered)
    
    return 100.0 * (total_delivered - total_returned) / total_requested

def get_bridge(lines, return_map, lo, hi):
    # Base: Contract (Lines, Confirmed, No returns deduction, Requested Delivery Date)
    # Step 1: Date Window (Requested Delivery Date -> Despatch Date)
    # Step 2: Denominator (Confirmed -> Requested)
    # Step 3: Returns (None -> Deducted)
    # Step 4: Aggregation (Lines -> Units)
    
    # Note: Using use_amended=False for bridge base
    c_lines = [l for l in lines if lo <= l['requested_delivery_date'] < hi]
    s_lines = [l for l in lines if l['despatch_date'] and lo <= l['despatch_date'] < hi]
    
    def get_rate(lines_set, use_units, use_requested, deduct_returns):
        if not lines_set: return 0
        if use_units:
            denom = sum(l['requested_qty'] if use_requested else l['confirmed_qty'] for l in lines_set)
            if denom == 0: return 0
            num = sum(l['delivered_qty'] - (return_map.get(l['line_id'], 0) if deduct_returns else 0) for l in lines_set)
            return 100.0 * num / denom
        else:
            denom = len(lines_set)
            num = 0
            for l in lines_set:
                conf = l['requested_qty'] if use_requested else l['confirmed_qty']
                if conf is None: continue
                deliv = l['delivered_qty'] - (return_map.get(l['line_id'], 0) if deduct_returns else 0)
                if deliv >= conf:
                    num += 1
            return 100.0 * num / denom

    rate_0 = get_rate(c_lines, False, False, False)
    rate_1 = get_rate(s_lines, False, False, False)
    rate_2 = get_rate(s_lines, False, True, False)
    rate_3 = get_rate(s_lines, False, True, True)
    rate_4 = get_rate(s_lines, True, True, True)
    
    return {
        "date_window": round(rate_1 - rate_0, 2),
        "denominator": round(rate_2 - rate_1, 2),
        "returns_treatment": round(rate_3 - rate_2, 2),
        "aggregation": round(rate_4 - rate_3, 2),
        "other": 0.0
    }
