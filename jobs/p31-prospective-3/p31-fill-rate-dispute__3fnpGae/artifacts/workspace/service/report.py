import json
import os
import csv

from service import metrics

def write_report(db_path, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    con = metrics.connect(db_path)
    try:
        lo, hi = metrics.period(con)
        lines, return_map, ticket_list, account_list = metrics.get_base_data(con, lo, hi)
        
        # Contract fill rate with ambiguity (Schedule 4)
        rate_low, lines_n, filled_low = metrics.calculate_contract_fill(lines, lo, hi, use_amended=False)
        rate_high, _, filled_high = metrics.calculate_contract_fill(lines, lo, hi, use_amended=True)
        
        # Supplier definition
        supplier_rate = metrics.calculate_supplier_fill(lines, return_map, lo, hi)
        
        # Bridge
        bridge = metrics.get_bridge(lines, return_map, lo, hi)
        
        # Published rate (from DB)
        published_row = con.execute("SELECT value FROM published_metrics WHERE source = 'MRG demand science'").fetchone()
        published_rate = published_row['value'] if published_row else None
        
        # Per account results (using standard basis)
        per_account_json = {}
        account_rows = []
        accounts_below_floor = 0
        for acc in account_list:
            acc_id = acc['account_id']
            r, n, f = metrics.calculate_contract_fill(lines, lo, hi, account_id=acc_id, use_amended=False)
            if r is None:
                continue
            
            per_account_json[acc_id] = round(r, 2)
            below = 1 if r < acc['service_floor_pct'] else 0
            if below:
                accounts_below_floor += 1
            
            account_rows.append({
                "account_id": acc_id,
                "lines": n,
                "lines_filled": f,
                "fill_rate_pct": round(r, 2),
                "below_floor": below
            })
            
        # Returns driven ticket share
        ticket_lines = [t['line_id'] for t in ticket_list]
        tickets_with_returns = sum(1 for tid in ticket_lines if tid in return_map)
        returns_share = 100.0 * tickets_with_returns / len(ticket_lines) if ticket_lines else 0.0
        
        # Verdict and Decisions
        # Since Schedule 4 is unexecuted, the exact contractual figure is not determinable.
        verdict = "not_determinable_from_available_evidence"
        bonus_gate_met = "not_determinable"
        supplier_claim_payable = "not_determinable"
        
        readout = {
            "period": [lo, hi],
            "fill_rate_contract_pct": round(rate_low, 2),
            "fill_rate_contract_low_pct": round(rate_low, 2),
            "fill_rate_contract_high_pct": round(rate_high, 2),
            "fill_rate_supplier_definition_pct": round(supplier_rate, 2),
            "published_rate_pct": round(published_rate, 2) if published_rate else None,
            "bridge_pp": bridge,
            "account_fill_pct": per_account_json,
            "accounts_below_floor": accounts_below_floor,
            "returns_driven_ticket_share_pct": round(returns_share, 2),
            "governing_definition": "contract_line_fill_confirmed",
            "incumbent_verdict": verdict,
            "bonus_gate_met": bonus_gate_met,
            "supplier_claim_payable": supplier_claim_payable
        }
        
        with open(os.path.join(out_dir, "readout.json"), "w") as fh:
            json.dump(readout, fh, indent=2, sort_keys=True)
            fh.write("\n")
            
        with open(os.path.join(out_dir, "account_fill.csv"), "w", newline='') as fh:
            writer = csv.DictWriter(fh, fieldnames=["account_id", "lines", "lines_filled", "fill_rate_pct", "below_floor"])
            writer.writeheader()
            writer.writerows(account_rows)
            
    finally:
        con.close()
