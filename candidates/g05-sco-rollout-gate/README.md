# G05: SCO 2.0 tranche-2 continuation gate (maintainer notes)

Generation-3 candidate (causal inference; staggered rollout). Not agent-visible: only `environment/workspace/` plus the
generated warehouse, reports, notebook and house outputs reach the image.

**Decision.** A grocery chain decides whether to fund waves 5–6 of a self-checkout redesign. The business case gate is
the expected run-rate uplift in weekly net sales for the stores still to be installed, with their planned kit, versus a
2.5% hurdle.

**Attractors.**
- The Programme team's house readout (static TWFE on log basket size, planned dates, all weeks) reports +5.5% baskets
  (wave 1 +7.7%).
- FP&A's quick check (unconditional store + week imputation, all weeks, pooled live stores) reports +6.6% net sales.
- Both say continue. The true gate figure on the visible warehouse is +1.1%: stop.

**Repair.**
1. Build the panel from the install log (actual go-live) and comparable trading weeks (no closure record).
2. Estimate untreated outcomes conditional on format (the sequencing variable), avoiding base periods inside the
   install closures.
3. Average store run-rate effects (weeks 13–26 after go-live).
4. Transport to waves 5–6 by kit version (the big-basket lane needs a rear bay; bay stores went first).
5. Report bootstrap intervals and the decision.

**Links.**
- Re-audit and redesign: `research/g05/G05_research_audit.md`.
- Phase-0 simulation gate (passed in round 4; every round recorded): `research/g05/G05_phase0_gate.md`.
- Fixture audit: `research/g05/fixture_audit.json`.
- Validation report: `report/g05_prebaseline_validation.md`.

## Layout

| Path | Purpose |
|---|---|
| `instruction.md` | CFO memo (agent-visible) |
| `environment/Dockerfile` | multi-stage build; generator and history run in a discarded build stage |
| `environment/build/world.py` | deterministic stdlib generator: stores, layout survey, plan, install log, closures, weekly KPIs, exact potential-outcome effects |
| `environment/build/history.py` | house readout, Programme report, FP&A notebook |
| `environment/workspace/` | faulty `sco_readout` package, docs, notes |
| `solution/` | oracle (`solve.sh`, `sco_readout/{panel,estimate,report,cli}.py`) |
| `tests/test.sh` | sandboxed verifier entry point (copied from G24's hardened version) |
| `tests/test_readout.py` | exact panel checks and tolerance checks on the visible and 3 hidden warehouses |
| `tests/world.py` | copy of `environment/build/world.py` (keep identical) |
| `tests/scenarios.py` | hidden warehouse specs and frozen reference standard errors |

## Dev tools (`tools/g05/`)

| Tool | Purpose |
|---|---|
| `fixture_audit.py N OUT.json` | Monte-Carlo SE_ref per extract (writes `SE_REF` into `tests/scenarios.py`), and every accepted and wrong analysis measured on the frozen extracts |
| `quickcheck.py build CACHE` / `run CACHE IMPL` | grade `workspace:DIR`, `variant:METHOD` or `variantjson:JSON` with the verifier's checks |
| `variant_cli.py` | drop-in `cli.py` running any Phase-0 estimator or mutation on the warehouse |
| `alt_*.py` | independently written correct implementations |
| `shortcuts.py --docker IMAGE` | mutation suite in the task image with the real `test.sh` |

After editing `environment/build/world.py`, copy it to `tests/world.py`, then rerun the fixture audit and every check.
