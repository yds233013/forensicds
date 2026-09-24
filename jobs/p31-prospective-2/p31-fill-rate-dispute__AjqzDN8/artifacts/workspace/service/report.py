"""Writes required outputs for the category service-level report."""
import json
import os
import csv

from service import metrics


def write_report(db_path, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    con = metrics.connect(db_path)
    try:
        lo, hi = metrics.get_period(con)
        
        # Contract rates
        rate_low, _, _ = metrics.get_contract_fill_rate(con, lo, hi, basis='original')
        rate_high, _, _ = metrics.get_contract_fill_rate(con, lo, hi, basis='amended')
        
        # Supplier rate
        rate_supplier = metrics.get_supplier_fill_rate(con, lo, hi)
        
        # Published rate
        pub_row = con.execute("SELECT value FROM published_metrics WHERE source = 'MRG demand science'").fetchone()
        published_rate = pub_row['value'] if pub_row else None
        
        # Bridge
        bridge = metrics.get_bridge(con, lo, hi)
        
        # Accounts
        per_account, below_count = {}, 0
        account_rows = []
        for a in metrics.get_accounts(con):
            r, n, f = metrics.get_contract_fill_rate(con, lo, hi, basis='original', account_id=a["account_id"])
            if r is None:
                continue
            
            below = 1 if r < a["service_floor_pct"] else 0
            per_account[a["account_id"]] = round(r, 2)
            if below:
                below_count += 1
            
            account_rows.append({
                "account_id": a["account_id"],
                "lines": n,
                "lines_filled": f,
                "fill_rate_pct": round(r, 2),
                "below_floor": below
            })
            
        # Decision Logic
        governing = "contract_line_fill_confirmed"
        rate_contract = rate_low # Basis A is the executed one
        
        # Verdict: Schedule 4 is not executed, so Basis A is the only one that governs.
        # However, the contract acknowledges the ambiguity.
        # But if the published figure matches Basis A, it's correct under the executed agreement.
        incumbent_verdict = "incumbent_correct" if round(rate_contract, 2) == round(published_rate, 2) else "incumbent_incorrect"
        
        bonus_gate_met = "yes" if rate_contract >= 96.0 else "no"
        
        # Supplier claim: payable where category figure is below 95%
        supplier_claim_payable = "yes" if rate_contract < 95.0 else "no"
        
        readout = {
            "period": [lo, hi],
            "fill_rate_contract_pct": round(rate_contract, 2),
            "fill_rate_contract_low_pct": round(rate_low, 2),
            "fill_rate_contract_high_pct": round(rate_high, 2),
            "fill_rate_supplier_definition_pct": round(rate_supplier, 2),
            "published_rate_pct": round(published_rate, 2),
            "bridge_pp": bridge,
            "account_fill_pct": per_account,
            "accounts_below_floor": below_count,
            "returns_driven_ticket_share_pct": round(metrics.get_ticket_share(con), 2),
            "governing_definition": governing,
            "incumbent_verdict": incumbent_verdict,
            "bonus_gate_met": bonus_gate_met,
            "supplier_claim_payable": supplier_claim_payable,
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
