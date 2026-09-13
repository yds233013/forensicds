"""Hidden generalization fixtures (never present in the agent's environment).

Each spec is a different synthetic company snapshot: different seed, calendar,
account ids, close month and migration patterns. Only a fix that implements the
documented identity semantics (canonical account via billing ownership + effective
migration lineage, one mapping row per billing account) reproduces the reference
on all of them.
"""

HIDDEN_SPECS = [
    {
        # Novel patterns: staged->staged chain (triple multiplication for a naive
        # as-of join), 3-way consolidation, staged cutover whose successor carries no
        # legacy links and whose legacy record closes mid-month (a naive join *drops*
        # revenue), a migration effective in the open period (history restated but no
        # reported months affected), identifiers that look like migrated accounts.
        "name": "hidden_a",
        "seed": 5501,
        "go_live": "2025-01-01",
        "close_month": "2025-11",
        "extract_date": "2025-12-02",
        "segments": {"Enterprise": 18, "Mid-Market": 45, "SMB": 70},
        "new_customer_share": 0.2,
        "id_base": {"account": 300000, "billing": 410000},
        "fx": {
            "EUR": {"base": 1.04, "walk": 0.007, "shocks": {"2025-06": 0.03}},
            "GBP": {"base": 1.25, "walk": 0.006, "shocks": {}},
        },
        "price_changes": [],
        "realignments": [{"date": "2025-07-01", "share": 0.25}],
        "incidents": [{"date": "2025-10-21", "n_accounts": 12, "credit_pct": 0.15,
                       "issue_after_days": [2, 8], "force_migrated_legacy": 3}],
        "similar_ids": 2,
        "migrations": [
            {"kind": "single", "style": "closed", "effective": "2025-04-01", "copy_links": True,
             "select": {"segment": "Mid-Market", "billing": "monthly_only"}},
            {"kind": "chain", "select": {"segment": "Enterprise", "billing": "has_annual", "size_rank": 2},
             "hops": [{"style": "staged", "effective": "2025-08-11", "cutover_closed": None, "copy_links": True},
                      {"style": "staged", "effective": "2025-11-03", "cutover_closed": None, "copy_links": True}]},
            {"kind": "consolidation", "n_sources": 3, "style": "staged", "effective": "2025-10-06",
             "cutover_closed": None, "copy_links": True,
             "select": {"segment": "Enterprise", "billing": "has_annual", "size_rank": 4}},
            {"kind": "single", "style": "staged", "effective": "2025-09-15", "cutover_closed": "2025-10-20",
             "copy_links": False, "select": {"segment": "Enterprise", "billing": "has_annual", "size_rank": 0}},
            {"kind": "single", "style": "staged", "effective": "2025-12-01", "cutover_closed": None,
             "copy_links": True, "select": {"segment": "Mid-Market", "billing": "has_annual", "size_rank": 1}},
            {"kind": "scheduled", "effective": "2025-12-15",
             "select": {"segment": "Enterprise", "billing": "has_annual", "size_rank": 1}},
        ],
    },
    {
        # Different year and close month; month-end boundary (legacy record closes on the
        # last day of the month), consolidation of monthly customers with immediate
        # cutover, price change at a different date.
        "name": "hidden_b",
        "seed": 9127,
        "go_live": "2024-07-01",
        "close_month": "2025-03",
        "extract_date": "2025-04-03",
        "segments": {"Enterprise": 14, "Mid-Market": 40, "SMB": 60},
        "new_customer_share": 0.25,
        "id_base": {"account": 500000, "billing": 610000},
        "fx": {
            "EUR": {"base": 1.09, "walk": 0.005, "shocks": {"2025-03": -0.025}},
            "GBP": {"base": 1.27, "walk": 0.005, "shocks": {}},
        },
        "price_changes": [{"plan_code": "GROWTH_M", "effective": "2025-01-01", "unit_price_minor": 5200}],
        "realignments": [{"date": "2025-01-01", "share": 0.2}],
        "incidents": [],
        "similar_ids": 1,
        "migrations": [
            {"kind": "single", "style": "closed", "effective": "2024-11-01", "copy_links": False,
             "select": {"segment": "Mid-Market", "billing": "monthly_only"}},
            {"kind": "consolidation", "n_sources": 2, "style": "closed", "effective": "2025-01-01",
             "copy_links": True, "select": {"segment": "Mid-Market", "billing": "monthly_only"}},
            {"kind": "single", "style": "closed", "effective": "2025-02-01", "copy_links": True,
             "select": {"segment": "SMB", "billing": "monthly_only"}},
            {"kind": "single", "style": "staged", "effective": "2025-03-10", "cutover_closed": "2025-03-31",
             "copy_links": True, "select": {"segment": "Enterprise", "billing": "has_annual", "size_rank": 1}},
        ],
    },
    {
        # A company with no migrations at all (empty register): the repaired pipeline
        # must still work and match billing exactly.
        "name": "hidden_c",
        "seed": 314,
        "go_live": "2026-01-01",
        "close_month": "2026-06",
        "extract_date": "2026-07-02",
        "segments": {"Enterprise": 8, "Mid-Market": 20, "SMB": 30},
        "new_customer_share": 0.3,
        "id_base": {"account": 700000, "billing": 810000},
        "fx": {
            "EUR": {"base": 1.12, "walk": 0.004, "shocks": {}},
            "GBP": {"base": 1.31, "walk": 0.004, "shocks": {}},
        },
        "price_changes": [],
        "realignments": [{"date": "2026-04-01", "share": 0.3}],
        "incidents": [{"date": "2026-05-05", "n_accounts": 6, "credit_pct": 0.1,
                       "issue_after_days": [1, 5], "force_migrated_legacy": 0}],
        "similar_ids": 0,
        "migrations": [],
    },
]
