**To:** Marketplace Analytics
**From:** VP Marketplace Operations
**Re:** FY27 commitment on Priority Dispatch - which number do we sign?

Merchant Growth want Priority Dispatch available to every merchant from the start of FY27, and they
have written the FY27 plan on the pilot readout in
`reports/priority_dispatch_pilot_readout.md` - priority stores fulfilled **+16.6 points** more of
their demand than everyone else.

Courier Ops do not accept it. Their point is blunt: we did not add a single courier for this pilot,
and couriers are a fixed pool in a city on a day. If a priority store got more of its orders out,
somebody else in that city got fewer of theirs out. They want to know what is left once everybody
has it.

Finance will fund the build only if the improvement under the proposed rollout clears +1.5 points.
I need that number, the supporting effects, and the recommendation that follows. Start with
`README.md`.

Requirements:

1. `cd /workspace && python -m dispatch_experiment analyse --warehouse data/warehouse.sqlite --out out`
   must write `analysis_results.json` as specified in `docs/outputs/analysis_contract.md`.
2. The same command is re-run against each pilot extract, so the method must hold in general: no
   special-casing of particular merchants, cities, dates or values in this extract.
3. `data/warehouse.sqlite` is the system of record: do not modify it, and do not hand-edit outputs
   or reports.
4. Re-running on the same extract must give identical outputs.
5. Leave the outputs regenerated for this extract, and tell me briefly whether the readout number
   should go to Finance as it stands.
