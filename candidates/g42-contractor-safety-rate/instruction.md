**To:** HSE Reporting
**From:** VP Operations
**Re:** The client's access review on Monday — which rate do we send?

Our published report for the window puts the recordable rate at 1.26 against the 1.50 access limit,
and concludes no action. The operator's auditor has come back with a rate above the limit and a draft
notice suspending new work at three sites.

I need to know which of us is right before Monday, and I am told the answer is not a matter of
opinion: the contract adopts the recordkeeping standard, and the standard says what a recordable case
is and what hours worked are. `docs/recordable_case_standard.md` and `docs/hours_worked_policy.md` are
the operative definitions; `notes/hse_notes.md` has what the site leads have raised. Start with
`README.md`.

If we are above the limit I would rather know it from you than from the auditor.

Requirements:

1. `cd /workspace && python -m safety_rate rate --warehouse data/warehouse.sqlite --out out` must write
   `readout.json` and `site_rates.csv` as specified in `docs/outputs/rate_contract.md`.
2. The same command is re-run against each monthly extract, so the method must hold in general: no
   special-casing of particular sites, workers, cases, dates or values in this extract.
3. `data/warehouse.sqlite` is the system of record: do not modify it, and do not hand-edit outputs or
   reports.
4. Re-running on the same extract must give identical outputs.
5. Leave the outputs regenerated for this window, and tell me briefly whether we are above the limit
   and what the published report was counting that it should not have been.
