**To:** Analytics
**From:** Chief Risk Officer
**Re:** Northwater certificate — their counsel has rejected it

Northwater's counsel has rejected our Q2 certificate. Their position is that clause 3.2 is written on
*their* traffic, that the 99.8% in our certificate is the marketing panel, and that the 94.8% is our
own book. They have asked for the figure on their traffic, and they are hinting at the remediation
clause.

I need our own answer before we respond, computed from the quarter's production evidence as clause 3.3
requires. `docs/screening_service_agreement.md` is the agreement, `docs/review_queue_sop.md` is how the
queue is fed, and `notes/fraud_ops_notes.md` is what the floor has been telling us. Start with
`README.md`.

If we are below the floor, say so plainly — I would rather remediate than argue and lose.

Requirements:

1. `cd /workspace && python -m screen_perf report --warehouse data/warehouse.sqlite --out out` must
   write `performance.json` as specified in `docs/outputs/performance_contract.md`.
2. The same command is re-run each quarter and for other merchants, so the method must hold in general:
   no special-casing of particular transactions, reviewers, dates or values in this extract.
3. `data/warehouse.sqlite` is the system of record: do not modify it, and do not hand-edit outputs or
   reports.
4. Re-running on the same extract must give identical outputs.
5. Leave the outputs regenerated for this quarter, and tell me briefly whether we certify or remediate,
   and why the two figures in the published certificate are not the contract figure.
