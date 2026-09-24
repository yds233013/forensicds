import sqlite3
import json
from statistics import mean, pstdev

def analyze():
    con = sqlite3.connect("data/inspection.sqlite")
    con.row_factory = sqlite3.Row
    
    # Post window parts
    rows = con.execute("""
        SELECT r.*, h.family AS heat_family 
        FROM inspection_results r 
        JOIN heats h ON h.heat_id = r.heat_id 
        WHERE r.week BETWEEN 19 AND 24
    """).fetchall()
    
    machines = ["CMM-1", "CMM-2"]
    stats = {}
    for m in machines:
        m_rows = [r for r in rows if r['machine_id'] == m]
        fails = [r for r in m_rows if r['disposition'] == 'FAIL']
        m_measured = [r['measured_um'] for r in m_rows]
        
        stats[m] = {
            "count": len(m_rows),
            "fail_rate": 100.0 * len(fails) / len(m_rows) if m_rows else 0,
            "mean": mean(m_measured) if m_measured else 0,
            "pstdev": pstdev(m_measured) if m_measured else 0
        }
        
    # By family in post window
    families = ["H2", "H3"]
    fam_stats = {}
    for f in families:
        f_rows = [r for r in rows if r['heat_family'] == f]
        fails = [r for r in f_rows if r['disposition'] == 'FAIL']
        f_measured = [r['measured_um'] for r in f_rows]
        fam_stats[f] = {
            "count": len(f_rows),
            "fail_rate": 100.0 * len(fails) / len(f_rows) if f_rows else 0,
            "mean": mean(f_measured) if f_measured else 0
        }

    # Interaction
    inter_stats = {}
    for m in machines:
        for f in families:
            mf_rows = [r for r in rows if r['machine_id'] == m and r['heat_family'] == f]
            fails = [r for r in mf_rows if r['disposition'] == 'FAIL']
            inter_stats[f"{m}_{f}"] = {
                "count": len(mf_rows),
                "fail_rate": 100.0 * len(fails) / len(mf_rows) if mf_rows else 0
            }

    con.close()
    return {
        "by_machine": stats,
        "by_family": fam_stats,
        "interaction": inter_stats
    }

print(json.dumps(analyze(), indent=2))
