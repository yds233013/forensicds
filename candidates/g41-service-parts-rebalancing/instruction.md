**To:** Field Service Planning
**From:** Service Director
**Re:** Week of 22 September — do we raise the expedite or not?

The planner's run on this week's extract comes back clean: no shortfall, 53 units moved, no expedite.
On that basis I sign nothing and we absorb the week by rescheduling.

The depot managers tell me a different story. `notes/depot_notes.md` has the detail — parts sitting
on a QA hold, stock already spoken for by jobs in flight, a container that will not be put away in
time. If they are right, the gap is real and the expedite rule in the service contract has already
been crossed, and that purchase has to be raised on Monday to land at all.

The expedite is expensive and audited, so I need the number it stands on to be the one the policy
actually defines: the smallest shortfall we can get to with the parts we can genuinely issue and the
moves we can genuinely make, and the cheapest plan that gets there. Start with `README.md`;
`docs/parts_availability_policy.md` is the contract.

Requirements:

1. `cd /workspace && python -m service_parts plan --warehouse data/warehouse.sqlite --out out` must
   write `plan.csv` and `readout.json` as specified in `docs/outputs/plan_contract.md`.
2. The same command is re-run against each weekly extract, so the method must hold in general: no
   special-casing of particular depots, parts, jobs, dates or values in this extract.
3. `data/warehouse.sqlite` is the system of record: do not modify it, and do not hand-edit outputs
   or reports.
4. Re-running on the same extract must give identical outputs.
5. Leave the outputs regenerated for this extract, and tell me briefly whether we expedite and what
   the published run was counting that it should not have been.
