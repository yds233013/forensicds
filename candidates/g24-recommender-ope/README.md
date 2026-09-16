# G24: off-policy evaluation of home-row rankers (maintainer notes)

Generation-3 candidate. Not agent-visible: only `environment/workspace/` plus the generated log extract, reports,
notebook and gate outputs reach the image.

**Incident.**
- A streaming service's offline gate replays candidate rankers on the production ranker's own responses and scores
  only the slots where a candidate agrees with what was shown.
- It rates v7 at +12% and v7_pd at +18% over production v6. AB-1182 measured v7 at −4% online, with no sample-ratio
  problem.
- v7_pd has never been tested online.

**Repair.**
1. Reconstruct slate decisions from cached re-serves (TTL per session and surface).
2. Recognise what the exploration stream randomized. It is a uniform ordering of the titles that survive the
   downstream rules layer, so the item-in-slot marginal is 1/m with m the eligible count. It is not the pre-filter
   slate probability the ranker logs.
3. Build counterfactual rows from eligible titles.
4. Estimate with slot-exact IPS, or an accepted equivalent: position transfer, doubly robust, self-normalised, or
   on-policy means where a stream exists.
5. Report paired intervals and apply the launch rule.

**Links.**
- Research audit: `research/g24/G24_research_audit.md`.
- Phase-0 simulation gate (passed; pre-registered tolerances): `research/g24/G24_phase0_gate.md`.
- Validation report: `report/g24_prebaseline_validation.md`.

## Layout

| Path | Purpose |
|---|---|
| `instruction.md` | stakeholder memo (agent-visible) |
| `environment/Dockerfile` | multi-stage build: generator and history run in a build stage; the final image holds the workspace only |
| `environment/build/world.py` | deterministic stdlib generator (sessions, pools, rules-layer suppression, streams, cache re-serves, position-based clicks) |
| `environment/build/history.py` | runs the deployed gate; writes the gate reports, the AB-1182 readout and the June IPS notebook |
| `environment/workspace/` | faulty `recs_eval` package, serving extract and config, docs, notes |
| `solution/` | oracle (`solve.sh`, `recs_eval/{ope,cli,yaml_lite}.py`) |
| `tests/test.sh` | sandboxed verifier entry point (pipeline as uid 65534; `/tests` 700; runtime manifest; fail-closed) |
| `tests/test_ope.py` | behavioural checks on the visible and 3 hidden extracts, graded immediately per run (memory) |
| `tests/truth.py` | generator truth: decision table, target slates, exact values, analytic SE of slot-exact IPS |
| `tests/world.py` | copy of `environment/build/world.py` (keep identical) |
| `tests/scenarios.py` | hidden extract specs |
| `tests/runtime_manifest.sha256` | sha256 manifest of the pinned base image's interpreter, stdlib and sandbox tools |

## Dev tools (`tools/g24/`)

| Tool | Purpose |
|---|---|
| `make_workspace.sh DIR` / `local_verify.sh DIR` | materialise the agent workspace; run the verifier locally |
| `quickcheck.py build CACHE` / `run CACHE IMPL` | build the four graded extracts with truth; grade `workspace:DIR`, `variant:METHOD`, `variantjson:JSON` or `file:CLI.py` |
| `variant_ope.py` | parameterised accepted and wrong estimators and overfits (mutation suite) |
| `alt_pandas_pbm.py` | independently written correct implementation (pandas, position transfer, seeded bootstrap) |
| `shortcuts.py --docker IMAGE` | mutation suite in the task image with the real `test.sh` |

After editing `environment/build/world.py`, copy it to `tests/world.py`, rebuild the quickcheck cache, and re-grade
every method before rerunning the mutation suite.
