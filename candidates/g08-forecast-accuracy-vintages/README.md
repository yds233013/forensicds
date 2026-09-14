# G08: forecast accuracy under settlement vintages (maintainer notes)

Generation-3 candidate. Not agent-visible: only `environment/workspace/` plus the generated warehouse and reports
reach the image.

- **Incident:** an electricity supplier's forecast accuracy mart replaced a KPI-pack notebook whose inputs were retired.
  The mart evaluates historical forecasts against the wrong versions of both sides:
  - latest settlement run of any type, instead of the Initial Settlement charge basis as it stood at the delivery
    month's KPI close;
  - latest forecast issued, instead of the set locked at the 11:00 UK gate;
  - current portfolio dimension, instead of membership effective on the delivery day;
  - run-month KPI months;
  - unsettled forecasts dropped;
  - models compared over different periods.
- **Design:** `research/g08/G08_build_design.md`.
- **Validation report:** `report/g08_prebaseline_validation.md`.

## Layout

| Path | Purpose |
|---|---|
| `instruction.md` | stakeholder memo (agent-visible) |
| `environment/Dockerfile` | multi-stage build: generator and history run in a build stage; final image holds the workspace only |
| `environment/build/world.py` | deterministic stdlib generator (warehouse, pack history, pack markdowns, ops dashboard) |
| `environment/build/history.py` | runs the deployed mart at the extract instant and writes the September accuracy review |
| `environment/workspace/` | faulty mart, docs, legacy notebook, notes, incident log |
| `solution/` | oracle (`solve.sh`, `fcaccuracy/mart.py`, `fcaccuracy/kpi.py`) |
| `tests/test.sh` | sandboxed verifier entry point (pipeline as uid 65534; `/tests` 700) |
| `tests/test_accuracy_mart.py` | behavioural checks: visible extract + 3 hidden extracts |
| `tests/reference.py` | independent stdlib reference computed from the warehouse only |
| `tests/world.py` | copy of `environment/build/world.py` (keep identical) |
| `tests/scenarios.py` | hidden extract specs |

## Dev tools (`tools/g08/`)

| Tool | Purpose |
|---|---|
| `make_workspace.sh DIR` | materialise the agent workspace locally |
| `local_verify.sh DIR` | run the verifier against a local workspace |
| `calibrate.py` | build an extract; check the reference against the generator; measure wrong repairs |
| `quickcheck.py IMPL DIR...` | compare an implementation with the reference on extracts |
| `variant_mart.py` | parameterised correct/wrong mart used by the mutation suite |
| `alt_sqlite.py`, `alt_replay.py` | independently structured correct implementations |
| `shortcuts.py --docker IMAGE` | mutation suite in the task image with the real `test.sh` |

After editing `environment/build/world.py`, copy it to `tests/world.py`.
