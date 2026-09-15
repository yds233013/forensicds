# G10: unconstrained demand under informative stockout censoring (maintainer notes)

Generation-3 candidate. Not agent-visible: only `environment/workspace/` plus the generated warehouse, reports, notebook
and field note reach the image.

**Incident.** A grocer's demand review (demandsci 2.3) takes recorded sales as demand and computes category baselines
on "clean" stockout-free days. The LEAN-26 working-capital programme cut order-up-to levels in 12 of 16 stores, which
now sell out on high-demand days. The review shows all eight category baselines falling (ice cream included, while its
sales rise) and zero lost sales. The finance readout quotes a clean-day fill-in estimate of about 2% lost sales and recommends
extending the programme.

**Repair.** Build the unconstrained expected demand history:
- in-stock intervals;
- day-type traffic profile from uncensored days;
- traffic-weighted exposure;
- NB likelihood with in-stock exposure offset;
- posterior imputation.

Then baselines on all non-promotional days, and programme impact (lost units and share, production forecast bias
against demand).

**Links.**
- Research audit: `research/g10/G10_research_audit.md`.
- Design (with as-built deltas in §0): `research/g10/G10_build_design.md`.
- Tolerance pilot (hard gate, passed): `research/g10/G10_tolerance_pilot.md`.
- Tolerances as installed: pre-registered recalibration on the task generator, `research/g10/recal/` (round 2 passed).
- Validation report: `report/g10_prebaseline_validation.md`.

## Layout

| Path | Purpose |
|---|---|
| `instruction.md` | stakeholder memo (agent-visible) |
| `environment/Dockerfile` | multi-stage build: generator and history run in a build stage; final image holds the workspace only |
| `environment/build/world.py` | deterministic stdlib generator (warehouse, competitor field note) |
| `environment/build/history.py` | runs the deployed review and writes the category review, availability KPI, week-8 readout and July notebook |
| `environment/workspace/` | faulty `demandsci` package, docs, notes, SQL |
| `solution/` | oracle (`solve.sh`, `demandsci/{warehouse,demand,trends}.py`) |
| `tests/test.sh` | sandboxed verifier entry point (pipeline as uid 65534; `/tests` 700) |
| `tests/test_demand_review.py` | behavioural checks: visible extract + 3 hidden extracts, graded against realised demand |
| `tests/truth.py` | graded aggregates from the generator's realised arrivals |
| `tests/tolerances.json` | per-quantity tolerances from the round-2 recalibration (`research/g10/recal/RESULT_ROUND2.md`) |
| `tests/runtime_manifest.sha256` | sha256 manifest of the pinned base image's interpreter, stdlib and sandbox tools (regenerate if the base digest changes) |
| `tests/world.py` | copy of `environment/build/world.py` (keep identical) |
| `tests/scenarios.py` | hidden extract specs |

## Dev tools (`tools/g10/`)

| Tool | Purpose |
|---|---|
| `make_workspace.sh DIR` | materialise the agent workspace locally |
| `local_verify.sh DIR` | run the verifier against a local workspace |
| `quickcheck.py build CACHE` / `run CACHE IMPL [VARIANT]` | build the four graded extracts with truth once; grade an implementation with the verifier's check functions and print error/tolerance ratios |
| `variant_review.py` | parameterised correct and wrong estimators (mutation suite) |
| `alt_gibbs_review.py` | independently structured correct implementation (Gibbs data augmentation) |
| `shortcuts.py --docker IMAGE` | mutation suite in the task image with the real `test.sh` |
| `recalibrate.py run/tolerances/summarize` | pre-registered tolerance calibration and validation on the task generator (`research/g10/recal/`) |
| `lrtest_dispersion.py EXTRACT...` | likelihood checks on graded extracts: per-category vs common dispersion; NB vs Poisson-lognormal |

After editing `environment/build/world.py`, copy it to `tests/world.py`. If the generator changes, rebuild the cache
and rerun quickcheck for every method before rerunning the mutation suite.
