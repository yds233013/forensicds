"""Point-in-time audit for renewal-risk examples (oracle helper).

Independently of the pipeline code, recomputes with SQL (window functions over the field-history
tables) the CRM stage / forecast and CS health color / score each example should see at its
prediction time - the latest change loaded (synced_at) before 00:00 UTC on the prediction date - and
compares with what the current-state tables say (--diagnose) or with artifacts/features.csv.
"""
import sqlite3
import sys

import pandas as pd

STAGE = {"Closed Lost": 0, "Qualification": 1, "Discovery": 2, "Proposal": 3, "Negotiation": 4, "Verbal": 5, "Closed Won": 6}
DIAGNOSE = "--diagnose" in sys.argv

con = sqlite3.connect("file:data/warehouse.db?mode=ro", uri=True)
ex = pd.read_csv("artifacts/examples.csv")
con.execute("CREATE TEMP TABLE ex (contract_id TEXT, account_id TEXT, cutoff TEXT)")
con.executemany("INSERT INTO ex VALUES (?,?,?)", [(r.contract_id, r.account_id, f"{r.prediction_date} 00:00:00")
                                                   for r in ex.itertuples()])
as_of_sql = """
WITH hist AS (
  SELECT e.contract_id, h.field, h.new_value,
         ROW_NUMBER() OVER (PARTITION BY e.contract_id, h.field ORDER BY h.synced_at DESC, h.changed_at DESC) AS rn
  FROM ex e JOIN {entity_join} JOIN {table} h ON h.{key} = {entity_col}
  WHERE h.synced_at < e.cutoff
)
SELECT contract_id, field, new_value FROM hist WHERE rn = 1
"""
opp = pd.read_sql_query(as_of_sql.format(entity_join="crm_opportunities o ON o.contract_id = e.contract_id AND o.opportunity_type = 'renewal'",
                                         table="crm_opportunity_field_history", key="opportunity_id", entity_col="o.opportunity_id"), con)
hl = pd.read_sql_query(as_of_sql.format(entity_join="(SELECT 1) ", table="cs_account_health_history", key="account_id",
                                        entity_col="e.account_id").replace("JOIN (SELECT 1)  JOIN", "JOIN"), con)
asof = pd.concat([opp, hl]).pivot_table(index="contract_id", columns="field", values="new_value", aggfunc="first")
asof = asof.reindex(ex["contract_id"])
want = pd.DataFrame({
    "renewal_stage_ordinal": asof["stage"].map(STAGE).fillna(-1).astype(int),
    "forecast_omitted": (asof["forecast_category"] == "Omitted").astype(int),
    "health_red": (asof["health_color"] == "Red").astype(int),
    "health_score": pd.to_numeric(asof["health_score"]).fillna(50.0),
})

if DIAGNOSE:
    cur = pd.read_sql_query("SELECT e.contract_id, o.stage, o.forecast_category, h.health_color, h.health_score FROM ex e "
                            "LEFT JOIN crm_opportunities o ON o.contract_id = e.contract_id AND o.opportunity_type='renewal' "
                            "LEFT JOIN cs_account_health h ON h.account_id = e.account_id", con).set_index("contract_id")
    print("examples whose current-state value differs from the value known at prediction time:")
    print("  renewal stage     ", int((cur["stage"].map(STAGE).fillna(-1).astype(int) != want["renewal_stage_ordinal"]).sum()))
    print("  forecast omitted  ", int(((cur["forecast_category"] == "Omitted").astype(int) != want["forecast_omitted"]).sum()))
    print("  health red        ", int(((cur["health_color"] == "Red").astype(int) != want["health_red"]).sum()))
    print("  health score      ", int((cur["health_score"].astype(float) != want["health_score"]).sum()), "of", len(ex))
    sys.exit(0)

got = pd.read_csv("artifacts/features.csv").set_index("contract_id").reindex(ex["contract_id"])
bad = {c: int((got[c].astype(float) != want[c].astype(float)).sum()) for c in want.columns}
print("point-in-time audit mismatches:", bad)
if any(bad.values()):
    sys.exit(1)
print("point-in-time audit passed")
