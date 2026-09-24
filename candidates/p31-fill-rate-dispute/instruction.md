You are a demand-science analyst at Meridian Retail Group.

The Commercial Director has escalated the ambient-grocery service-level report (`reports/`). It publishes a
97.7% fill rate for the quarter; Brendale's own quarterly report, filed in `docs/`, shows 91.5% for the same
category and period; and three key accounts have logged shortfall tickets. He wants the metric rebuilt, the
demand-science team's bonus gate reviewed, and a position on a £1.8m claim against Brendale that turns on
whether the contractual account floor was breached.

Your job is to establish what the figure is on the basis that governs, account for the difference between the
two published numbers, and give a defensible position on each consequence. The `service` package in
`/workspace` produced the published figure; repair it where it is wrong and re-run it so the numbers are
reproducible. If it is not wrong, say so and show why.

`docs/outputs/readout_contract.md` specifies exactly what `out/readout.json` and `out/account_fill.csv` must
contain. `docs/` also holds the customer supply agreement, the supplier's methodology appendix and the table
dictionary; `notes/` holds category correspondence. `data/service.sqlite` is read-only.

Leave the package in place, with `python -m service fill --db data/service.sqlite --out out` producing the
outputs. Your position will be reviewed against the evidence in the workspace, so each figure and each
conclusion must be one the evidence supports.
