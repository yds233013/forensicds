# Evaluation outputs: specification

Owner: Personalisation Analytics. `python -m recs_eval ope --logs <db> --out <dir>` writes four files. Numbers are
written unrounded.

Definitions used below come from `docs/metrics/home_row.md`.

## `decisions.csv`

One row per slate decision and slot, for every decision in the extract (all streams, all devices).

| Column | Meaning |
|---|---|
| `decision_id` | the `serve_id` of the response that created the decision |
| `stream` | serving stream of the decision |
| `device` | device of the decision |
| `decided_at` | `served_at` of the response that created the decision |
| `position` | slot, 1–5 |
| `item_id` | the title the decision placed in that slot |
| `clicked` | 1 if the member clicked that slot of this decision, else 0 |

## `target_slates.csv`

The row each candidate ranker would have served, for every decision whose candidate list is in `rec_candidates`.
One row per decision, ranker and slot: `decision_id`, `policy` (`v6`, `v7`, `v7_pd`), `position`, `item_id`.

## `policy_values.csv`

One row per ranker (`v6`, `v7`, `v7_pd`):

| Column | Meaning |
|---|---|
| `value` | estimated home-row clicks per slate decision over the extract's decisions if that ranker had served them |
| `ci_low`, `ci_high` | 95% interval for `value` |
| `lift_vs_v6` | estimated difference in clicks per decision against the production ranker (0 for `v6`) |
| `lift_ci_low`, `lift_ci_high` | 95% interval for the lift |

## `launch.json`

`{"launch": "v6" | "v7" | "v7_pd"}` applying `docs/launch_policy.md` (`v6` means keep the production ranker).

Model scores are unique within a request, so a ranker's row is determined by its scores.
